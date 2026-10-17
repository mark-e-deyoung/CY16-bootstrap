// Independently authored synthetic timing model. NOT DE2-115 bridge RTL.
module synthetic_turnaround #(parameter integer CYCLES=8, parameter integer EARLY_EXIT=1)
 (input wire clk, rst, start, access, output reg busy, output reg done);
 integer remaining;
 always @(posedge clk) begin
  if (rst) begin busy<=0;done<=0;remaining<=0;end
  else begin
   done<=0;
   if (!busy && start) begin busy<=1;remaining<=CYCLES;end
   else if (busy) begin
    if (((EARLY_EXIT != 0) && !access) || remaining<=1) begin busy<=0;done<=1;end
    else remaining<=remaining-1;
   end
  end
 end
endmodule

module tb;
 reg clk=0,rst=1,start=0,access=0;
 wire busy_early,done_early,busy_full,done_full;
 integer e=-1,f=-1,i;
 synthetic_turnaround #(.CYCLES(8),.EARLY_EXIT(1)) early(clk,rst,start,access,busy_early,done_early);
 synthetic_turnaround #(.CYCLES(8),.EARLY_EXIT(0)) full(clk,rst,start,access,busy_full,done_full);
 always #10 clk=~clk; // 50 MHz
 initial begin
  repeat(2) @(negedge clk); rst=0;start=1;access=1;
  @(negedge clk);start=0;access=0;
  for(i=1;i<=12;i=i+1) begin
   @(negedge clk);
   if(done_early && e<0) e=i;
   if(done_full && f<0) f=i;
  end
  $display("synthetic early_exit_cycles=%0d full_count_cycles=%0d",e,f);
  if(e!=1 || f!=8) $fatal(1,"unexpected synthetic oracle measurements");
  $display("PASS synthetic control; private RTL NOT tested");
  $finish;
 end
endmodule
