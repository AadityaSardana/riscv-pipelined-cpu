content = open('src/dcache.sv','w')
content.write("""module dcache (
    input  logic        clk,
    input  logic        rst,
    input  logic [31:0] addr,
    input  logic        rd_en,
    input  logic        wr_en,
    input  logic [31:0] wr_data,
    input  logic [2:0]  funct3,
    output logic [31:0] data_out,
    output logic        stall,
    output logic [31:0] perf_hits,
    output logic [31:0] perf_misses,
    output logic [31:0] perf_accesses
);
    localparam LINES     = 256;
    localparam MEM_DELAY = 3;
    logic [31:0] c_data  [0:LINES-1];
    logic [21:0] c_tag   [0:LINES-1];
    logic        c_valid [0:LINES-1];
    logic [31:0] main_mem [0:4095];
    wire [21:0] a_tag    = addr[31:10];
    wire [7:0]  a_index  = addr[9:2];
    wire [11:0] m_index  = addr[13:2];
    wire hit_w = c_valid[a_index] && (c_tag[a_index] == a_tag);

    // Read cache and memory into plain wires first
    // so Icarus can do part-selects on them
    wire [31:0] raw      = c_data[a_index];
    wire [31:0] mem_raw  = main_mem[m_index];

    // Read data with sign/zero extension
    always_comb begin
        case (funct3)
            3'b000: data_out = {{24{raw[7]}},  raw[7:0]};
            3'b001: data_out = {{16{raw[15]}}, raw[15:0]};
            3'b010: data_out = raw;
            3'b100: data_out = {24'd0, raw[7:0]};
            3'b101: data_out = {16'd0, raw[15:0]};
            default:data_out = raw;
        endcase
    end

    assign stall = rd_en && !hit_w;

    logic [31:0] hit_count, miss_count, acc_count;
    assign perf_hits     = hit_count;
    assign perf_misses   = miss_count;
    assign perf_accesses = acc_count;

    // Write word construction using plain wires (no array part-select)
    wire [31:0] wr_cache_word = (funct3==3'b000) ? {raw[31:8],    wr_data[7:0]}  :
                                (funct3==3'b001) ? {raw[31:16],   wr_data[15:0]} :
                                                    wr_data;

    wire [31:0] wr_mem_word   = (funct3==3'b000) ? {mem_raw[31:8],  wr_data[7:0]}  :
                                (funct3==3'b001) ? {mem_raw[31:16], wr_data[15:0]} :
                                                    wr_data;

    localparam S_IDLE = 1'b0;
    localparam S_MISS = 1'b1;
    logic       state;
    logic [2:0] miss_cnt;
    logic       just_filled;

    integer i;
    always_ff @(posedge clk or posedge rst) begin
        if (rst) begin
            for (i=0; i<LINES; i=i+1) begin
                c_valid[i] <= 1'b0;
                c_tag[i]   <= 22'd0;
                c_data[i]  <= 32'd0;
            end
            state       <= S_IDLE;
            miss_cnt    <= 3'd0;
            just_filled <= 1'b0;
            hit_count   <= 32'd0;
            miss_count  <= 32'd0;
            acc_count   <= 32'd0;
        end else begin
            case (state)
                S_IDLE: begin
                    just_filled <= 1'b0;
                    if (wr_en) begin
                        acc_count         <= acc_count + 1;
                        main_mem[m_index] <= wr_mem_word;
                        if (hit_w) begin
                            hit_count       <= hit_count + 1;
                            c_data[a_index] <= wr_cache_word;
                        end else
                            miss_count <= miss_count + 1;
                    end else if (rd_en && !just_filled) begin
                        acc_count <= acc_count + 1;
                        if (hit_w)
                            hit_count <= hit_count + 1;
                        else begin
                            miss_count <= miss_count + 1;
                            miss_cnt   <= MEM_DELAY - 1;
                            state      <= S_MISS;
                        end
                    end
                end
                S_MISS: begin
                    if (miss_cnt == 3'd0) begin
                        c_data[a_index]  <= main_mem[m_index];
                        c_tag[a_index]   <= a_tag;
                        c_valid[a_index] <= 1'b1;
                        just_filled      <= 1'b1;
                        state            <= S_IDLE;
                    end else
                        miss_cnt <= miss_cnt - 1;
                end
                default: state <= S_IDLE;
            endcase
        end
    end
endmodule""")
content.close()
print('dcache.sv written!')
