content = open('src/icache.sv','w')
content.write("""module icache (
    input  logic        clk,
    input  logic        rst,
    input  logic [31:0] addr,
    input  logic        rd_en,
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
    wire [21:0] a_tag   = addr[31:10];
    wire [7:0]  a_index = addr[9:2];
    wire hit_w = c_valid[a_index] && (c_tag[a_index] == a_tag);
    assign data_out = hit_w ? c_data[a_index] : 32'd0;
    assign stall    = rd_en && !hit_w;
    logic [31:0] hit_count, miss_count, acc_count;
    assign perf_hits     = hit_count;
    assign perf_misses   = miss_count;
    assign perf_accesses = acc_count;
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
            state <= S_IDLE; miss_cnt <= 3'd0;
            just_filled <= 1'b0;
            hit_count <= 32'd0; miss_count <= 32'd0; acc_count <= 32'd0;
        end else begin
            case (state)
                S_IDLE: begin
                    just_filled <= 1'b0;
                    if (rd_en && !just_filled) begin
                        acc_count <= acc_count + 1;
                        if (hit_w) hit_count <= hit_count + 1;
                        else begin
                            miss_count <= miss_count + 1;
                            miss_cnt   <= MEM_DELAY - 1;
                            state      <= S_MISS;
                        end
                    end
                end
                S_MISS: begin
                    if (miss_cnt == 3'd0) begin
                        c_data[a_index]  <= main_mem[addr[13:2]];
                        c_tag[a_index]   <= a_tag;
                        c_valid[a_index] <= 1'b1;
                        just_filled      <= 1'b1;
                        state            <= S_IDLE;
                    end else miss_cnt <= miss_cnt - 1;
                end
                default: state <= S_IDLE;
            endcase
        end
    end
endmodule""")
content.close()
print('icache.sv written!')
