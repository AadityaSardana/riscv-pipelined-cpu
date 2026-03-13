module icache #(
    parameter LINES     = 256,
    parameter MEM_DELAY = 3
)(
    input  logic        clk,
    input  logic        rst,
    input  logic [31:0] addr,
    input  logic        rd_en,
    output logic [31:0] data_out,
    output logic        stall,
    output logic [9:0]  mem_rd_addr,
    input  logic [31:0] mem_rd_data,
    output logic [31:0] perf_hits,
    output logic [31:0] perf_misses,
    output logic [31:0] perf_acc
);
    logic        c_valid [0:LINES-1];
    logic [21:0] c_tag   [0:LINES-1];
    logic [31:0] c_data  [0:LINES-1];

    wire [21:0] a_tag   = addr[31:10];
    wire [7:0]  a_index = addr[9:2];
    wire hit_w = c_valid[a_index] && (c_tag[a_index] == a_tag);

    wire [31:0] cur_word = c_data[a_index];
    assign data_out    = (rd_en && hit_w) ? cur_word : 32'd0;
    assign stall       = rd_en && !hit_w;
    assign mem_rd_addr = addr[11:2];

    typedef enum logic [0:0] {S_IDLE, S_MISS} state_t;
    state_t state;
    logic [2:0] miss_cnt;
    integer i;

    always_ff @(posedge clk) begin
        if (rst) begin
            state       <= S_IDLE;
            miss_cnt    <= 0;
            perf_hits   <= 0;
            perf_misses <= 0;
            perf_acc    <= 0;
            for (i = 0; i < LINES; i = i+1) begin
                c_valid[i] = 1'b0;
                c_tag[i]   = 0;
                c_data[i]  = 0;
            end
        end else begin
            case (state)
                S_IDLE: begin
                    if (rd_en) begin
                        perf_acc <= perf_acc + 1;
                        if (hit_w)
                            perf_hits <= perf_hits + 1;
                        else begin
                            perf_misses <= perf_misses + 1;
                            miss_cnt    <= MEM_DELAY - 1;
                            state       <= S_MISS;
                        end
                    end
                end
                S_MISS: begin
                    if (miss_cnt == 0) begin
                        c_data[a_index]  <= mem_rd_data;
                        c_tag[a_index]   <= a_tag;
                        c_valid[a_index] <= 1'b1;
                        state            <= S_IDLE;
                    end else
                        miss_cnt <= miss_cnt - 1;
                end
            endcase
        end
    end
endmodule
