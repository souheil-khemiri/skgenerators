//started compiling this piece of shit meaningless tiny code with 22 errrors
package adderPlus
//import chipyard._//contains RocketConfig
import chisel3._//contains blackbox
//import chipyard.config._//contains RockerConfig => this is probably wrong
import chisel3.util._//contains HasBlackBoxResource
import chisel3.experimental.IntParam//contains IntParam
import freechips.rocketchip.tile._//contains lazyRoCC, OpcodeSet, lazyRoCCModuleImp
import org.chipsalliance.cde.config._// contains parameters, contains config
import org.chipsalliance.diplomacy.lazymodule._//contains lazymodule
import os.write.over
import firrtl.PrimOps.Add
//import chipyard.config.RocketConfig
//1. Add verilog blackbox
//1.2 define a bundle that describes the interface of the blackbox
//all the parameters are passed down to the IO even if they are not used in the IO
class AdderPlusIO(val WIDTH : Int, val PLUS : Int) extends Bundle {
    val  clk = Input(Clock())//
    val  rst = Input(Bool())//
    val  a = Input(UInt(WIDTH.W))//
    val  b = Input(UInt(WIDTH.W))//
    val  start = Input(Bool())
    val  valid = Output(Bool())//
    val  sum = Output(UInt(WIDTH.W))//
    val  ready = Output(Bool())//
}
//1.3 define the blackbox itself
class AdderPlusBB(val WIDTH : Int, val PLUS : Int) extends BlackBox(
    Map(
        "WIDTH" -> IntParam(WIDTH),
        "PLUS" -> IntParam(PLUS)
    )
) with HasBlackBoxResource {
  override def desiredName = "AdderPlus" // override the name of the blackbox class to martch the verilog module name
  val io = IO(new AdderPlusIO(WIDTH, PLUS))
  addResource("/vsrc/rtl/AdderPlus.v")
}

/*
this is the way rocc modules are defined and instantiated.
RoCC modules are instantiated via modules that extend the LazyRoCC class .
=> In this case, the AdderPlus class(this is the class that you use in the config).
These modules lazily instantiate another module which extends the LazyRoCCModuleImp class
=> In this case, the AdderPlusImp class.
The LazyRoCCModuleImp class is the one that contains the actual logic of the module.
*/
class AdderPlus(val WIDTH: Int, val PLUS: Int, opcodes: OpcodeSet)
    (implicit p: Parameters) extends LazyRoCC(opcodes) {
  override lazy val module = new AdderPlusImp(this)
    }

class AdderPlusImp(outer: AdderPlus)(implicit p: Parameters) extends LazyRoCCModuleImp(outer) {
  //instantiate the blackbox
  val AdderInst = Module(new AdderPlusBB(outer.WIDTH, outer.PLUS))

  //connect the blackbox to the IO of the module
  AdderInst.io.clk := clock
  printf("AdderPlusImp: system incoming clock signal= %d\n", clock.asUInt)
  printf("AdderPlusImp: adder clock signal= %d\n", AdderInst.io.clk.asUInt)

  AdderInst.io.rst := reset.asBool
  // command channel
  AdderInst.io.a := io.cmd.bits.rs1.asUInt
  AdderInst.io.b := io.cmd.bits.rs2.asUInt
  AdderInst.io.start := io.cmd.valid
  io.cmd.ready := AdderInst.io.ready

  // response channel
  io.resp.bits.data := AdderInst.io.sum
  io.resp.valid := AdderInst.io.valid

  //busy signal
  io.busy := AdderInst.io.start || (AdderInst.io.valid === false.B && AdderInst.io.ready === false.B)  

}

//config for the AdderPlus module
class WithAdderPlus(width: Int, plus: Int) extends Config((site, here, up) => {
  case BuildRoCC => up(BuildRoCC) ++ Seq(
    (p: Parameters) => LazyModule(new AdderPlus(width, plus, OpcodeSet.custom0)(p))
  )
  })

// //custom config with adder plus and a rocket core
// class AdderPlusRocketConfig extends Config(
//   new WithAdderPlus(width = 32, plus = 1) ++
//   new RocketConfig
// )



















  // val io = IO(new RoCCCommandIO(outer))
  // val adder = Module(new AdderPlusBB(outer.WIDTH, outer.PLUS))
  // adder.io.clk := clock
  // adder.io.rst := reset
  // adder.io.a := io.rs1
  // adder.io.b := io.rs2
  // adder.io.start := io.cmd.fire
  // io.cmd.ready := adder.io.ready
  // io.resp.valid := adder.io.valid
  // io.resp.bits.rd := io.cmd.bits.inst.rd
  // io.resp.bits.data := adder.io.sum
  // adder.io.valid := io.resp.fire
  // io.busy := adder.io.valid
  // io.interrupt := false.B // No interrupts in this example
  // // Add any additional logic here if needed
  // // For example, you can handle the PLUS parameter if needed
  // if (outer.PLUS > 0) {
  //   // Logic that uses the PLUS parameter
  // } else {
  //   // Logic that does not use the PLUS parameter
  // }
  // // You can also add additional ports to the AdderPlusIO if needed
  // if (outer.PLUS > 10) {
  //   adder.io.needsAttention.get := false.B // Example usage of the optional port
  // }
  // else {
  //   adder.io.needsAttention.get := true.B // Example usage of the optional port
  // }
  // // You can also add additional logic here if needed
  // // For example, you can handle the PLUS parameter if needed
  // if (outer.PLUS > 0) {
  //   // Logic that uses the PLUS parameter
  // } else {
  //   // Logic that does not use the PLUS parameter
  // }
  // // You can also add additional ports to the AdderPlusIO if needed
  // if (outer.PLUS > 10) {
  //   adder.io.needsAttention.get := false.B // Example usage of the optional port
  // }
  // else {
  //   adder.io.needsAttention.get := true.B // Example usage of the optional port
  // }
  // // You can also add additional logic here if needed
  // // For example, you can handle the PLUS parameter if needed
  // if (outer.PLUS > 0) {
  //   // Logic that uses the PLUS parameter
  // } else {
  //   // Logic that does not use the PLUS parameter
  // }
  // // You can also add additional ports to the AdderPlusIO if needed
  // if (outer.PLUS > 10) {
  //   adder.io.needsAttention.get := false.B // Example usage of the optional port
  // }
  // else {
  //   adder.io.needsAttention.get := true.B // Example usage of the optional port
  // }     