module bht #(
    parameter ENTRIES = 256   // 256 x 2-bit counters
)(
    input  logic        clk,
    input  logic        rst,

    // Predict port (IF stage)
    input  logic [31:0] pc,
    output logic        predict_taken,
    output logic [31:0] predict_target,
    input  logic [31:0] imm_b,         // branch offset from IF

    // Update port (EX stage)
    input  logic        update_en,     // 1 when branch resolves
    input  logic [31:0] update_pc,     // PC of the branch
    input  logic        actually_taken,// actual outcome

    // Performance counters
    output logic [31:0] perf_predictions,
    output logic [31:0] perf_mispredicts
);
    // 256 x 2-bit saturating counters
    logic [1:0] bht_table [0:ENTRIES-1];

    // Index = PC bits [9:2] (8 bits = 256 entries)
    wire [7:0] pred_idx   = pc[9:2];
    wire [7:0] update_idx = update_pc[9:2];

    // Predict — combinational
    assign predict_taken  = bht_table[pred_idx][1];  // MSB = prediction
    assign predict_target = pc + imm_b;              // branch target

    // Update — sequential
    integer i;
    always_ff @(posedge clk) begin
        if (rst) begin
            perf_predictions <= 0;
            perf_mispredicts <= 0;
            for (i = 0; i < ENTRIES; i = i+1)
                bht_table[i] = 2'b01;  // init = Weakly Not Taken
        end else begin
            if (update_en) begin
                perf_predictions <= perf_predictions + 1;

                // Check if we mispredicted
                if (bht_table[update_idx][1] != actually_taken)
                    perf_mispredicts <= perf_mispredicts + 1;

                // Update saturating counter
                if (actually_taken) begin
                    // increment toward Strongly Taken (11)
                    if (bht_table[update_idx] != 2'b11)
                        bht_table[update_idx] <= bht_table[update_idx] + 1;
                end else begin
                    // decrement toward Strongly Not Taken (00)
                    if (bht_table[update_idx] != 2'b00)
                        bht_table[update_idx] <= bht_table[update_idx] - 1;
                end
            end
        end
    end
endmodule
