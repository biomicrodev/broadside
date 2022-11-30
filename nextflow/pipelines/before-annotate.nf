import java.nio.file.Paths
import broadside.Scene
import broadside.Slide

include { PREPARE_CUBE_ALIGNMENTS } from "./prepare-cube-alignment"
include { PREPARE_ROUNDS } from "./prepare-rounds"
include { PROCESS_SCENES } from "./process-scenes"

// required inputs
params.slide = ""

// optional inputs
params.rounds = ""
params.scenes = ""

// validate inputs
def selectedRoundNames = params.rounds ? params.rounds.tokenize(" ") : null
def selectedSceneNames = params.scenes ? params.scenes.tokenize(" ") : null
def slide = new Slide(
    Paths.get(params.slide),
    selectedSceneNames as Set,
    selectedRoundNames as Set
)

// log init
log.info """\
==================================================================
B R O A D S I D E
Image processing pipeline for the
Laboratory for Bio-Micro Devices @ Brigham & Women's Hospital
------------------------------------------------------------------
*BEFORE* ANNOTATION
Run started: ${new Date()}

Running with the following settings:
${slide.nextflowStatus()}
==================================================================\
"""

workflow {
    PREPARE_CUBE_ALIGNMENTS()
    PREPARE_ROUNDS(slide, PREPARE_CUBE_ALIGNMENTS.out.timestamps)
    PROCESS_SCENES(slide, PREPARE_ROUNDS.out.illumProfilesByRound)
}
