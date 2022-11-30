package broadside.utils

import broadside.Slide

import java.nio.file.Paths

def slidePath = Paths.get(args[0])
def slide = new Slide(slidePath)
println(slide.detailedSummary())
