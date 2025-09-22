package skgenerators
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

    // State machine implementation
    val s_idle :: s_compute :: s_resp :: Nil = Enum(3)
    val state = RegInit(s_idle)
    //Accelerator input(to store rs1 and rs2) and output registers
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


//Simple Adder with parameters

class AdderParamAccelerator(opcodes: OpcodeSet, val param : Int)(implicit p : Parameters) extends LazyRoCC(opcodes){
    override lazy val module = new  AdderParamAcceleratorImp(this)
}
class AdderParamAcceleratorImp(outer: AdderParamAccelerator) extends LazyRoCCModuleImp(outer) with HasCoreParameters{
    val simpleAdderModuleInst = Module(new SimpleAdderModule)
    
    //io.cmd.bits.inst.rd register
    val rdReg = Reg(UInt(xLen.W))
    //rs1 and rs2 reg
    val inputAReg = Reg(UInt(xLen.W))
    val inputBReg = Reg(UInt(xLen.W))


    simpleAdderModuleInst.io.input_a := inputAReg
    simpleAdderModuleInst.io.input_b := inputBReg
    
    //result reg
    val resultReg = Reg(UInt(xLen.W))
    //response
    io.resp.bits.rd := rdReg
    io.resp.bits.data := resultReg
    //states
    val s_idle = 0.U(2.W)
    val s_compute = 1.U(2.W)
    val s_resp = 2.U(2.W)
    //state register, and state control
    val stateReg : UInt = RegInit(s_idle)
    io.cmd.ready := (stateReg === s_idle)
    io.resp.valid := (stateReg===s_resp)
    io.busy := (stateReg =/= s_idle)
    when(io.cmd.fire){
        rdReg:= io.cmd.bits.inst.rd
        inputAReg:=io.cmd.bits.rs1
        inputBReg:=io.cmd.bits.rs2
        stateReg:=s_compute
    }
    when(stateReg===s_compute){
        resultReg:= simpleAdderModuleInst.io.result + outer.param.asUInt
        stateReg:= s_resp
    }
    when(io.resp.fire){
        stateReg:=s_idle
    }

}

class WithAdderParamAccelerator(param : Int) extends Config((site, here, up) => {
    case BuildRoCC => Seq((p:Parameters) => LazyModule(
        new AdderParamAccelerator(OpcodeSet.custom0, param )(p)))
}

)






