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
 integer last_start=-1, wr_start=-1, rd_start=-1;
 integer cycle_violations=0,pulse_violations=0,starts=0,ends=0;
 always #10 clk=~clk; // 50 MHz synthetic host
 always @(negedge wr_n) begin
  if(cs_n || !rd_n) $fatal(1,"invalid synthetic write strobe");
  if(last_start>=0 && ($time-last_start)<125) cycle_violations=cycle_violations+1;
  last_start=$time;wr_start=$time;starts=starts+1;
 end
 always @(negedge rd_n) begin
  if(cs_n || !wr_n) $fatal(1,"invalid synthetic read strobe");
  if(last_start>=0 && ($time-last_start)<125) cycle_violations=cycle_violations+1;
  last_start=$time;rd_start=$time;starts=starts+1;
 end
 always @(posedge wr_n) begin
  if(wr_start>=0) begin
   if(($time-wr_start)<42) pulse_violations=pulse_violations+1;
   wr_start=-1;ends=ends+1;
  end
 end
 always @(posedge rd_n) begin
  if(rd_start>=0) begin
   if(($time-rd_start)<42) pulse_violations=pulse_violations+1;
   rd_start=-1;ends=ends+1;
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

module tb_hpi_cycle_contract;
 wire d2,d3,d7;
 hpi_case #(.ACCESS_CYCLES(2),.EXPECT_CYCLE_VIOLATIONS(5),
            .EXPECT_PULSE_VIOLATIONS(6)) too_short(d2);
 hpi_case #(.ACCESS_CYCLES(3),.EXPECT_CYCLE_VIOLATIONS(5),
            .EXPECT_PULSE_VIOLATIONS(0)) cycle_short(d3);
 hpi_case #(.ACCESS_CYCLES(7),.EXPECT_CYCLE_VIOLATIONS(0),
            .EXPECT_PULSE_VIOLATIONS(0)) meets_both(d7);
 initial begin
  wait(d2 && d3 && d7);
  $display("PASS source-backed synthetic HPI cycle and strobe controls; private RTL NOT tested");
  $finish;
 end
 initial begin #10000; $fatal(1,"synthetic timing test timed out"); end
endmodule
