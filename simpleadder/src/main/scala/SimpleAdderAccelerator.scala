package simpleadder
import chisel3._
import chisel3.util._
import freechips.rocketchip.tile._
import org.chipsalliance.cde.config._
import org.chipsalliance.diplomacy.lazymodule._
import org.chipsalliance.cde.config._


class SimpleAdderAccelerator(opcodes: OpcodeSet)(implicit p : Parameters) extends LazyRoCC(opcodes){
    override lazy val module = new  SimpleAdderAcceleratorModule(this)
}

class SimpleAdderAcceleratorModule(outer : SimpleAdderAccelerator) extends LazyRoCCModuleImp(outer) with HasCoreParameters{
    val simpleAdderModuleInst = Module(new SimpleAdderModule)

    // val regIoRespValid = RegInit(false.B)
    // val result = Reg(UInt(32.W))
    // val counter = RegInit(0.U(32.W))
    // val io_cmd_ready_reg = RegInit(false.B)
    // val io_cmd_bits_inst_rd_reg = RegInit(0.U(5.W))
    // counter := counter + 1.U

    // // io.cmd.ready := true.B
    // // io.resp.valid := false.B
    // //command channel
    // simpleAdderModuleInst.io.input_a := io.cmd.bits.rs1
    // simpleAdderModuleInst.io.input_b := io.cmd.bits.rs2

    // //response channel
    // io.resp.bits.data := result //simpleAdderModuleInst.io.result
    // io.resp.bits.rd   := io_cmd_bits_inst_rd_reg

    // //ctrl
    // io.cmd.ready := io_cmd_ready_reg //0
    // //io.cmd.ready := !regIoRespValid //1
    // io.resp.valid := regIoRespValid//0

    // when( io.cmd.valid && io.cmd.ready ){  //1 1
    //     printf("io.cmd.valid && io.cmd.ready")
    //     printf("counter = %d\n", counter)
    //     result := simpleAdderModuleInst.io.result
    //     regIoRespValid := true.B  //0  => io.cmd.ready = 0 and io.resp.valid = 1
    //     io_cmd_bits_inst_rd_reg := io.cmd.bits.inst.rd
    // }
    // when(io.resp.valid && io.resp.ready){// 1 
    //     printf("io.resp.valid && io.resp.ready")
    //     printf("counter = %d\n", counter)
    //     regIoRespValid := false.B
    // }
    // io.interrupt := false.B // no interrupts


    // State machine implementation
    val s_idle :: s_compute :: s_resp :: Nil = Enum(3)
    val state = RegInit(s_idle)
    //Accelerator input and output registers
    val result = Reg(UInt(xLen.W))
    val input_a_reg = Reg(UInt(xLen.W))
    val input_b_reg = Reg(UInt(xLen.W))
    
    //io.cmd.bits.inst.rd register
    val rd_reg = Reg(UInt(5.W))
    //cmd rs1 and rs2 
    simpleAdderModuleInst.io.input_a := input_a_reg
    simpleAdderModuleInst.io.input_b := input_b_reg
    //resp
    io.resp.bits.data := result
    io.resp.bits.rd   := rd_reg
    //state machine control
    io.resp.valid := (state === s_resp)
    io.cmd.ready := (state === s_idle)
    
    when(io.cmd.fire){
        state := s_compute
        rd_reg := io.cmd.bits.inst.rd
        input_a_reg := io.cmd.bits.rs1
        input_b_reg := io.cmd.bits.rs2
    }

    when (state === s_compute) {
        result := simpleAdderModuleInst.io.result
        state := s_resp
    }
    when (io.resp.fire) { state := s_idle }
    io.interrupt := false.B // no interrupts
    io.busy := (state =/= s_idle)


}

class WithSimpleAdderAccelerator extends Config((site, here, up) => {
    case BuildRoCC => Seq((p:Parameters) => LazyModule(
        new SimpleAdderAccelerator(OpcodeSet.custom0)(p)))
})

