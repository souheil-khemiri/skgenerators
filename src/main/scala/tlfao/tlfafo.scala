package skgenerators

import chisel3._
import chisel3.util._
import freechips.rocketchip.subsystem._
import org.chipsalliance.cde.config.{Parameters, Field, Config}
import org.chipsalliance.diplomacy.lazymodule._
import freechips.rocketchip.diplomacy.{IdRange}
import freechips.rocketchip.tilelink._
import freechips.rocketchip.tile._


class TlFafo(opcodes: OpcodeSet)(implicit p:Parameters) extends LazyRoCC(opcodes, nPTWPorts = 0){
  override val tlNode = TLClientNode(Seq(TLMasterPortParameters.v1(Seq(TLMasterParameters.v1(
        name="tlfafo",
        sourceId=IdRange(0,1))))))
    override lazy val module = new TlFafoModuleImp(this)
}

class TlFafoModuleImp(outer:TlFafo) extends LazyRoCCModuleImp(outer){
    val (tl, edge) = outer.tlNode.out(0)

    val sIdle :: sReq :: sWait :: sRespond :: Nil = Enum(4)
    val state = RegInit(sIdle)

    val baseAddr  = Reg(UInt(64.W))
    val fillValue = Reg(UInt(64.W))
    val addr      = Reg(UInt(64.W))
    val beatsLeft = Reg(UInt(32.W))
    val rdReg     = Reg(UInt(5.W))
    val respPending = Reg(Bool())

    val isConfig = io.cmd.bits.inst.funct === 0.U
    val isStart  = io.cmd.bits.inst.funct === 1.U

    io.cmd.ready := state === sIdle
    io.busy      := state =/= sIdle
    io.interrupt := false.B

    when (io.cmd.fire && isConfig) {
      baseAddr  := io.cmd.bits.rs1
      fillValue := io.cmd.bits.rs2
    }

    when (io.cmd.fire && isStart) {
      addr        := baseAddr
      beatsLeft   := io.cmd.bits.rs1
      rdReg       := io.cmd.bits.inst.rd
      respPending := io.cmd.bits.inst.xd   // only respond if the instr wants rd written
      state       := sReq
    }

    val (legal, putBundle) = edge.Put(
      fromSource = 0.U,
      toAddress  = addr,
      lgSize     = log2Ceil(edge.manager.beatBytes).U,
      data       = fillValue
    )
    tl.a.valid := state === sReq
    tl.a.bits  := putBundle
    assert(!tl.a.valid || legal, "Illegal TL request generated")

    when (tl.a.fire) {
      addr      := addr + edge.manager.beatBytes.U
      beatsLeft := beatsLeft - 1.U
      state     := sWait
    }

    tl.d.ready := state === sWait
    when (tl.d.fire) {
      state := Mux(beatsLeft === 0.U, sRespond, sReq)
    }

    io.resp.valid     := (state === sRespond) && respPending
    io.resp.bits.rd   := rdReg
    io.resp.bits.data := 0.U
    when (state === sRespond) {
      state := Mux(respPending, state, sIdle)  // stay until resp.fire if pending
      when (io.resp.fire || !respPending) { state := sIdle }
    }
}


class WithTlFafo extends Config((site, here, up) => {
  case BuildRoCC => up(BuildRoCC) ++ Seq(
    (p: Parameters) => {
      implicit val q = p
      LazyModule(new TlFafo(OpcodeSet.custom0))
    }
  )
})
