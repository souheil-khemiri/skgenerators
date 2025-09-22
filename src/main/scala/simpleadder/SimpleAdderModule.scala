package skgenerators
import chisel3._
import chisel3.util._

class SimpleAdderModule extends Module{
    val io = IO(new Bundle{
        val input_a = Input(UInt(32.W))
        val input_b = Input(UInt(32.W))
        val result = Output(UInt(32.W))
    })

    io.result := io.input_a + io.input_b
}