// Public, independently authored timing-contract fixture.
// This is NOT the DE2-115 bridge, a Cypress model, or hardware qualification.
// Datasheet: CY7C67200 38-08014 Rev J, HPI tCYC >= 6*(1/48MHz)
// and tWP/tRP >= 2*(1/48MHz). At 50 MHz: >=125ns and >=41.667ns.
`timescale 1ns/1ps
module hpi_case #(
 parameter integer ACCESS_CYCLES=7,
 parameter integer EXPECT_CYCLE_VIOLATIONS=0,
 parameter integer EXPECT_PULSE_VIOLATIONS=0
)(output reg done=0);
 reg clk=0,cs_n=1,wr_n=1,rd_n=1;
 time last_start=0, wr_start=0, rd_start=0;
 bit seen_start=0, seen_wr=0, seen_rd=0;
 integer cycle_violations=0,pulse_violations=0,starts=0,ends=0;
 always #10 clk=~clk; // 50 MHz synthetic host
 always @(negedge wr_n) begin
  if(cs_n || !rd_n) $fatal(1,"invalid synthetic write strobe");
  if(seen_start && ($time-last_start)<125) cycle_violations=cycle_violations+1;
  last_start=$time;seen_start=1;wr_start=$time;seen_wr=1;starts=starts+1;
 end
 always @(negedge rd_n) begin
  if(cs_n || !wr_n) $fatal(1,"invalid synthetic read strobe");
  if(seen_start && ($time-last_start)<125) cycle_violations=cycle_violations+1;
  last_start=$time;seen_start=1;rd_start=$time;seen_rd=1;starts=starts+1;
 end
 always @(posedge wr_n) begin
  if(seen_wr) begin
   if(($time-wr_start)<42) pulse_violations=pulse_violations+1;
   seen_wr=0;ends=ends+1;
  end
 end
 always @(posedge rd_n) begin
  if(seen_rd) begin
   if(($time-rd_start)<42) pulse_violations=pulse_violations+1;
   seen_rd=0;ends=ends+1;
  end
 end
 task automatic transaction(input bit write_dir);
  begin
   @(negedge clk);
   cs_n=0;
   if(write_dir) wr_n=0; else rd_n=0;
   repeat(ACCESS_CYCLES) @(negedge clk);
   if(write_dir) wr_n=1; else rd_n=1;
   cs_n=1;
  end
 endtask
 initial begin
  repeat(2) @(negedge clk);
  // WW, WR, RW, RR transition coverage, including back-to-back requests.
  transaction(1);transaction(1);transaction(0);
  transaction(1);transaction(0);transaction(0);
  #1;
  $display("contract access=%0d starts=%0d ends=%0d cycle_violations=%0d pulse_violations=%0d",
   ACCESS_CYCLES,starts,ends,cycle_violations,pulse_violations);
  if(starts!=6 || ends!=6 || cycle_violations!=EXPECT_CYCLE_VIOLATIONS ||
     pulse_violations!=EXPECT_PULSE_VIOLATIONS)
    $fatal(1,"synthetic HPI contract control mismatch");
  done=1;
 end
endmodule


// Independent, public-safe registered-pad OE control. This is a synthetic
// model, NOT the DE2-115/Terasic module or a substitute for private RTL HIL.
// The Cypress datasheet's write-data hold requirement is >= 2 ns.
// A write-gated OE releases data at the same simulated instant as nWR rises;
// a separate one-clock hold produces a measurable post-strobe window.
module synthetic_pad_write_hold #(
 parameter integer HOLD_CLOCKS=0
)(
 input wire clk, rst, start,
 output reg wr_n=1,
 output wire [15:0] data
);
 reg drive=0;
 reg [1:0] phase=0;
 assign data=drive ? 16'hA55A : 16'hzzzz;
 always @(posedge clk) begin
  if(rst) begin phase<=0; wr_n<=1; drive<=0; end
  else case(phase)
   0: if(start) begin drive<=1; wr_n<=0; phase<=1; end
   1: begin wr_n<=1; if(HOLD_CLOCKS==0) drive<=0; phase<=2; end
   2: begin if(HOLD_CLOCKS>0) drive<=0; phase<=3; end
   default: begin end
  endcase
 end
endmodule

module hpi_pad_hold_case #(
 parameter integer HOLD_CLOCKS=0,
 parameter integer EXPECT_HOLD_NS=0
)(output reg done=0);
 reg clk=0, rst=1, start=0;
 wire wr_n;
 wire [15:0] data;
 time rise_at=0, release_at=0;
 bit seen_low=0, seen_drive=0, seen_rise=0, seen_release=0;
 synthetic_pad_write_hold #(.HOLD_CLOCKS(HOLD_CLOCKS)) dut
  (.clk(clk),.rst(rst),.start(start),.wr_n(wr_n),.data(data));
 always #10 clk=~clk;
 always @(negedge wr_n) seen_low=1;
 always @(posedge wr_n) if(seen_low) begin rise_at=$time; seen_rise=1; end
 always @(data) begin
  if(data === 16'hA55A) seen_drive=1;
  else if(data === 16'hzzzz && seen_drive) begin
   release_at=$time; seen_release=1;
  end
 end
 initial begin
  repeat(2) @(negedge clk);
  rst=0; start=1;
  @(negedge clk); start=0;
  wait(seen_rise && seen_release);
  #1;
  $display("synthetic pad hold clocks=%0d rise=%0t release=%0t hold_ns=%0t",
   HOLD_CLOCKS,rise_at,release_at,release_at-rise_at);
  if(release_at-rise_at != EXPECT_HOLD_NS)
   $fatal(1,"synthetic registered pad OE hold control mismatch");
  done=1;
 end
 initial begin #1000; if(!done) $fatal(1,"synthetic pad hold control timed out"); end
endmodule

module tb_hpi_cycle_contract;
 wire d2,d3,d7,pad_zero,pad_held;
 hpi_pad_hold_case #(.HOLD_CLOCKS(0),.EXPECT_HOLD_NS(0)) no_hold(pad_zero);
 hpi_pad_hold_case #(.HOLD_CLOCKS(1),.EXPECT_HOLD_NS(20)) one_cycle_hold(pad_held);
 hpi_case #(.ACCESS_CYCLES(2),.EXPECT_CYCLE_VIOLATIONS(5),
            .EXPECT_PULSE_VIOLATIONS(6)) too_short(d2);
 hpi_case #(.ACCESS_CYCLES(3),.EXPECT_CYCLE_VIOLATIONS(5),
            .EXPECT_PULSE_VIOLATIONS(0)) cycle_short(d3);
 hpi_case #(.ACCESS_CYCLES(7),.EXPECT_CYCLE_VIOLATIONS(0),
            .EXPECT_PULSE_VIOLATIONS(0)) meets_both(d7);
 initial begin
  wait(d2 && d3 && d7 && pad_zero && pad_held);
  $display("PASS source-backed synthetic HPI cycle, strobe, and pad OE hold controls; private RTL NOT tested");
  $finish;
 end
 initial begin #10000; $fatal(1,"synthetic timing test timed out"); end
endmodule
