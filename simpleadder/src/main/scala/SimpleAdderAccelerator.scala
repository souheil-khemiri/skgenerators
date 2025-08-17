package simpleadder
import chisel3._
import freechips.rocketchip.tile._
import org.chipsalliance.cde.config._
import org.chipsalliance.diplomacy.lazymodule._
import org.chipsalliance.cde.config._

class SimpleAdderAccelerator(opcodes: OpcodeSet)(implicit p : Parameters) extends LazyRoCC(opcodes){
    override lazy val module = new  SimpleAdderAcceleratorModule(this)
}

class SimpleAdderAcceleratorModule(outer : SimpleAdderAccelerator) extends LazyRoCCModuleImp(outer){
    val simpleAdderModuleInst = Module(new SimpleAdderModule)

    val regIoRespValid = RegInit(false.B)

    io.cmd.ready := true.B
    io.resp.valid := false.B
    //command channel
    simpleAdderModuleInst.io.input_a := io.cmd.bits.rs1
    simpleAdderModuleInst.io.input_b := io.cmd.bits.rs2

    //response channel
    io.resp.bits.data := simpleAdderModuleInst.io.result
    io.resp.bits.rd   := io.cmd.bits.inst.rd

    //ctrl
    io.cmd.ready := !regIoRespValid
    io.resp.valid := regIoRespValid

    when( io.cmd.valid && io.cmd.ready ){
        regIoRespValid := true.B
    }
    when(io.resp.valid && io.resp.ready){
        regIoRespValid := false.B
    }
    io.interrupt := false.B // no interrupts
}

class WithSimpleAdderAccelerator extends Config((site, here, up) => {
    case BuildRoCC => Seq((p:Parameters) => LazyModule(
        new SimpleAdderAccelerator(OpcodeSet.custom0)(p)))
})

