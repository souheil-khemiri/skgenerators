package skgenerators

import chisel3._
import chisel3.util._
import freechips.rocketchip.tile._
import org.chipsalliance.cde.config._
import org.chipsalliance.diplomacy.lazymodule._
import org.chipsalliance.cde.config._
import chisel3.experimental.IntParam

class SimpleMCUIO(val xlen: Int) extends Bundle{
    val clock =Input(Clock())
    val reset =Input(Reset())
    val init_address =Input(UInt(xlen.W))
    val set_init_address =Input(Bool()) 
    val increment =Input(UInt(xlen.W))
    val set_increment =Input(Bool())
    val transfer_count =Input(UInt(xlen.W))
    val set_transfer_count =Input(Bool())
    val operation =Input(Bool())
    val set_operation =Input(Bool())
    val start =Input(Bool())
    val address_out =Output(UInt(xlen.W))
    val enable = Output(Bool())
    val rd_wr = Output(Bool())
    val busy = Output(Bool())
}

class SimpleMCU(val xlen: Int) extends BlackBox(Map("xlen" -> IntParam(xlen))) with HasBlackBoxResource{
    val io = IO(new SimpleMCUIO(xlen))
    addResource("/vsrc/SimpleMCU.v")
}

class SimpleMCUAcc(opcodes : OpcodeSet)(implicit p:Parameters) extends LazyRoCC(opcodes){
    override lazy val module = new SimpleMCUImp(this)
}

class SimpleMCUImp(outer : SimpleMCUAcc)(implicit p:Parameters) extends LazyRoCCModuleImp(outer) with HasCoreParameters{
    val SimpleMCUInst = Module(new SimpleMCU(xLen))
    val rd_reg = Reg(UInt(5.W))
    val resp_pending = RegInit(false.B)
    //clock and reset
    SimpleMCUInst.io.clock := clock
    SimpleMCUInst.io.reset := reset
    //functins cmd.bits.inst.funct
    val funct = io.cmd.bits.inst.funct
    val set_init_address = (0.U===funct)
    val set_increment = (1.U===funct)
    val set_transfer_count = (2.U===funct)
    val set_operation = (3.U===funct)
    val start = (4.U===funct)
    val get_last_address = (5.U===funct)
    //
    when(get_last_address && io.cmd.fire){ 
        rd_reg := io.cmd.bits.inst.rd
        resp_pending := true.B
    }
    when(io.resp.fire) {
        resp_pending := false.B
    }
    io.busy := SimpleMCUInst.io.busy || resp_pending
    io.cmd.ready := !SimpleMCUInst.io.busy
    io.resp.valid := resp_pending && !SimpleMCUInst.io.busy
    //
    SimpleMCUInst.io.set_init_address := set_init_address
    SimpleMCUInst.io.set_increment := set_increment
    SimpleMCUInst.io.set_transfer_count:= set_transfer_count
    SimpleMCUInst.io.set_operation := set_operation
    SimpleMCUInst.io.start := start 
    // rs1 input to mcu parameter signal
    SimpleMCUInst.io.init_address := io.cmd.bits.rs1
    SimpleMCUInst.io.increment := io.cmd.bits.rs1
    SimpleMCUInst.io.transfer_count := io.cmd.bits.rs1
    SimpleMCUInst.io.operation := io.cmd.bits.rs1(0).asBool
    //
    io.resp.bits.rd := rd_reg
    io.resp.bits.data := SimpleMCUInst.io.address_out
    //
    // when(set_init_address){
    //     SimpleMCUInst.io.init_address:=io.cmd.bits.rs1   
    // }.elsewhen(set_increment){
    //     SimpleMCUInst.io.increment:=io.cmd.bits.rs1
    // }.elsewhen(set_transfer_count){
    //     SimpleMCUInst.io.transfer_count:=io.cmd.bits.rs1                    
    // }.elsewhen(set_operation){
    //     SimpleMCUInst.io.operation := io.cmd.bits.rs1(0).asBool
    // }
    

}

class WithSimpleMCUAcc() extends Config((site, here, up) => {
    case BuildRoCC => Seq((p:Parameters) => LazyModule(
        new SimpleMCUAcc(OpcodeSet.custom0)(p)))
}
)

