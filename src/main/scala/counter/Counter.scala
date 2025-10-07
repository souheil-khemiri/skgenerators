package skgenerators
import chisel3._
import chisel3.util._
import freechips.rocketchip.tile._
import org.chipsalliance.cde.config._
import org.chipsalliance.diplomacy.lazymodule._
import org.chipsalliance.cde.config._
import chisel3.experimental.IntParam
import freechips.rocketchip.regmapper.RRTest0Map.re

class CounterIO(val xLen : Int) extends Bundle{
 val  clk = Input(Clock()) 
 val  start = Input(Bool()) 
 val  reset = Input (Reset()) 
 val  init_val = Input(UInt(xLen.W))
 val  init = Input(Bool())
 val  return_current_count = Input(Bool())
 val  current_count = Output(UInt(xLen.W))
 val  debug_out = Output(UInt(xLen.W))
 val  count_valid = Output(Bool())
 val count_valid_fsm = Output(Bool())
}

class counter(val xLen : Int) extends BlackBox(
    Map("xLen" -> IntParam(xLen))
) with HasBlackBoxResource{
    val io = IO(new CounterIO(xLen))
    addResource("/vsrc/counter.v")
}

class CounterAcc(opcodes: OpcodeSet, version: String = "v1") (implicit p: Parameters) extends LazyRoCC(opcodes){
    override lazy val module = version match {
        case "v1" => new CounterAccImp(this)
        case "v2" => new CounterAccImpV2(this)
    }
}

class CounterAccImp(outer : CounterAcc) (implicit p: Parameters) extends LazyRoCCModuleImp(outer) with HasCoreParameters {
    val counterInst = Module(new counter(xLen))
    val init_val_reg = Reg(UInt(xLen.W))
    //clock and reset
    counterInst.io.clk := clock
    counterInst.io.reset := reset
    //init value
    counterInst.io.init := false.B
    counterInst.io.start := false.B
    counterInst.io.return_current_count := false.B
    //functions cmd.bits.inst.funct
    val init = 0.U
    val start = 1.U
    val return_current_count = 2.U
    //cmd
    //registered function
    val funct = Reg(UInt(7.W)) 
    //take init_value from rs1
    //counterInst.io.init_val:= init_val_reg
    counterInst.io.init_val:= 0.U
    //current value goes to rd, needs to be registered
    val current_count_reg = Reg(UInt(xLen.W))
    current_count_reg := counterInst.io.current_count
    //rd register 
    val rd_reg = Reg(UInt(5.W))
    io.resp.bits.rd := rd_reg 
    // rocc interface fsm
    val s_idle = 0.U(2.W)
    val s_compute = 1.U(2.W)
    val s_wait = 2.U(2.W)
    val s_resp = 3.U(2.W)
    val stateReg : UInt = RegInit(s_idle)
    io.busy := (stateReg =/= s_idle )
    io.cmd.ready := (stateReg === s_idle)
    io.resp.valid := (stateReg === s_resp)

    when(io.cmd.fire){
        funct := io.cmd.bits.inst.funct
        when(io.cmd.bits.inst.funct === init){
            counterInst.io.init := true.B
            //init_val_reg := io.cmd.bits.rs1
            counterInst.io.init_val := io.cmd.bits.rs1
            stateReg := s_compute
        }
        .elsewhen(io.cmd.bits.inst.funct === start){
            counterInst.io.start := true.B
            stateReg := s_compute
        }
        .elsewhen(io.cmd.bits.inst.funct === return_current_count){
            counterInst.io.return_current_count:=true.B
            rd_reg := io.cmd.bits.inst.rd
            stateReg := s_compute
        }

    }

    when(stateReg === s_compute){
        when(funct === init){
            counterInst.io.init := false.B
            stateReg := s_idle
        }
        .elsewhen(funct === start){
            counterInst.io.start := false.B
            stateReg := s_idle
        }
        .elsewhen(funct === return_current_count){
            stateReg := s_wait
        }
        
    }
    
    when(stateReg === s_wait){
        stateReg := s_resp
    }

    when(io.resp.fire && funct === return_current_count){
        io.resp.bits.data := counterInst.io.current_count //current_count_reg 
        counterInst.io.return_current_count := false.B       
        stateReg := s_idle
    }
 }


/*
V2
Updated version of the counter.
Getting rid of unecessary states.
Cleaner and more understandable.
*/

class CounterAccImpV2(outer : CounterAcc) (implicit p: Parameters) extends LazyRoCCModuleImp(outer) with HasCoreParameters{
    val counterInst = Module(new counter(xLen))

    val rd_reg = Reg(UInt(5.W))
    //states to control io.cmd.ready
    val s_idle = 0.U
    val s_busy = 1.U
    val state = RegInit(s_idle) // 0: idle, 1: busy

    val funct = io.cmd.bits.inst.funct
    val init = (0.U===funct)
    val start = (1.U===funct)
    val return_current_count = (2.U===funct)
    val count_valid = counterInst.io.count_valid

    counterInst.io.clk := clock
    counterInst.io.reset := reset 

    /*setting all initial counter.io.{start, init, return_current_count} to 0
    because simulation gave the following error:
    [476645000] %Error: TestHarness.sv:99: Assertion failed in TOP.TestDriver.testHarness: Assertion failed: *** FAILED *** (exit code =          1)

    at SimTSI.scala:21 assert(!error, "*** FAILED *** (exit code = %%d)\n", exit >> 1.U)

    %Error: /home/souheil/chipyard/sims/verilator/generated-src/chipyard.harness.TestHarness.CounterRocketConfig/gen-collateral/TestHarness.sv:99: Verilog $stop
    Solution: set them inside cmd.fire --> dns (did not solve)
    checked V1 agin : works fine
    Solution 2: problem with the count_valid signal being always high =>  io.resp.valid always high


    */
    counterInst.io.start := false.B//start
    counterInst.io.init := false.B//init
    counterInst.io.return_current_count := false.B//return_current_count
    counterInst.io.init_val := io.cmd.bits.rs1
    io.resp.bits.data := counterInst.io.current_count
    io.resp.bits.rd := rd_reg

    io.cmd.ready := (state === s_idle)
    io.busy := (state =/= s_idle)
    io.resp.valid := count_valid
    

    when(io.cmd.fire){
        when(init){
            counterInst.io.init := true.B
        }
        .elsewhen(start){
            counterInst.io.start:= true.B
        }
        .elsewhen(return_current_count){
        counterInst.io.return_current_count := true.B
        rd_reg := io.cmd.bits.inst.rd
        state := s_busy  
        }
    }
    when(io.resp.fire){
        state := s_idle
    }

} 



class WithCounterAcc(version: String) extends Config((site, here, up) => {
    case BuildRoCC => Seq((p:Parameters) => LazyModule(
        new CounterAcc(OpcodeSet.custom0, version)(p)))
}
)
