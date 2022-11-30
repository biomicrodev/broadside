import java.nio.file.Path
import java.nio.file.Paths

// illumination-specific parameters
params.computeDarkfield = false
params.nMaxIllum = 200
params.overwriteIllumProfiles = false
params.nAssessIllum = 5

// unmix-specific parameters
params.nMosaic = 64
params.unmixMidChunkSize = 512
params.unmixDownsample = 8
params.overwriteUnmixingMosaic = false
params.refChannelIndex = 0

// local variables
def randomSeed = new Random(0)
def newline = "\n"

process GET_RANDOM_ILLUM_TILES_BY_ROUND {
    tag "round: ${round}"

    input:
        val slide
        val round

    output:
        tuple \
            val(round), \
            path("random-illum-tile-paths-${round}.txt")

    exec:
        def tilePaths = slide.getTilePathsForRound(round)
        tilePaths.shuffle(randomSeed)
        def nTiles = Math.min(params.nMaxIllum, tilePaths.size()).toInteger()
        def selectedTilePaths = tilePaths[0..<nTiles]
        def dst = task.workDir.resolve("random-illum-tile-paths-${round}.txt")
        file(dst).text = selectedTilePaths.join(newline)
}

process GET_ALL_ILLUM_TILES_BY_ROUND {
    tag "round: ${round}"

    input:
        val slide
        val round

    output:
        tuple \
            val(round), \
            path("all-illum-tile-paths-${round}.txt")

    exec:
        def dst = task.workDir.resolve("all-illum-tile-paths-${round}.txt")
        file(dst).text = slide.getTilePathsForRound(round).join(newline)
}

process MAKE_ILLUM_PROFILES_BY_ROUND {
    /*
    This step has a parallel step, where images are read in, and a serial step, where
    the flatfield and darkfield images are computed iteratively. The memory usage of
    this step is dependent on the number of tiles, but because it is essentially fixed,
    we don't expect to change this. Obviously this may change in the future, so if
    anyone changes the number of tiles picked for this step, the memory will have to
    change as well.

    As a rule of thumb, 200 images needed 4GB. Whether that scales linearly...
    */

    if (!workflow.stubRun) {
        conda "./envs/before-annotate-env.yml"
    }
    tag "round: ${round}"
    memory "4 GB"
    cpus 2

    publishDir(
        path: "${illumDir}",
        enabled: !workflow.stubRun,
        mode: "copy",
        pattern: "flatfield-*.tiff",
    )
    publishDir(
        path: "${illumDir}",
        enabled: !workflow.stubRun,
        mode: "copy",
        pattern: "darkfield-*.tiff",
    )
    // log dask performance reports
    publishDir(
        path: "${params.logDir}/illum-profiles/",
        enabled: !workflow.stubRun,
        mode: "copy",
        pattern: "make-illum-profiles-*.dask-performance.html",
    )

    input:
        tuple \
            val(round), \
            path(tilesPath)
        val illumDir

    output:
        tuple \
            val(round), \
            path("flatfield-${round}.tiff"), \
            path("darkfield-${round}.tiff"), emit: profiles
        path "make-illum-profiles-${round}.dask-performance.html", optional: true

    script:
        def darkDir = Paths.get(params.calibrationDir).resolve("dark")
        def darkfieldArg = params.computeDarkfield ? "--darkfield" : "--no-darkfield"
        """
        make-illum-profiles \
            --tiles-path "${tilesPath}" \
            --flatfield-path "flatfield-${round}.tiff" \
            --darkfield-path "darkfield-${round}.tiff" \
            "${darkfieldArg}" \
            --dark-dir "${darkDir}" \
            --dask-report-filename "make-illum-profiles-${round}.dask-performance.html" \
            --n-cpus "${task.cpus}" \
            --memory-limit "${task.memory}"
        """

    stub:
        """
        touch "flatfield-${round}.tiff"
        touch "darkfield-${round}.tiff"
        touch "make-illum-profiles-${round}.dask-performance.html"
        """
}

process GET_UNMIXING_TILES_BY_ROUND {
    tag "round: ${round}"

    input:
        val slide
        val round

    output:
        tuple \
            val(round), \
            path("unmix-mosaic-${round}.txt")

    exec:
        def dst = task.workDir.resolve("unmix-mosaic-${round}.txt")
        file(dst).text = slide.getTilePathsForRound(round).join(newline)
}

process MAKE_UNMIXING_MOSAIC_BY_ROUND {
    if (!workflow.stubRun) {
        conda "./envs/before-annotate-env.yml"
    }
    tag "round: ${round}"
    memory "4 GB"
    cpus 2

    publishDir(
        path: "${unmixDir}",
        mode: "copy",
        enabled: !workflow.stubRun,
        pattern: "unmixing-mosaic-*.tiff",
    )
    // log dask performance reports
    publishDir(
        path: "${params.logDir}/unmixing-mosaics/",
        enabled: !workflow.stubRun,
        mode: "copy",
        pattern: "make-unmixing-mosaic-*.dask-performance.html",
    )

    input:
        tuple \
            val(round), \
            path(flatfieldPath), \
            path(darkfieldPath), \
            path(tilesPath)
        val unmixDir

    output:
        path "unmixing-mosaic-${round}.tiff"
        path "make-unmixing-mosaic-${round}.dask-performance.html"

    script:
        def darkDir = Paths.get(params.calibrationDir).resolve("dark")
        def scalesShiftsDir = Paths.get(params.calibrationDir).resolve("cube-alignment").resolve("scales-shifts")
        """
        make-unmixing-mosaic \
            --tiles-path "${tilesPath}" \
            --n-tiles "${params.nMosaic}" \
            --flatfield-path "${flatfieldPath}" \
            --darkfield-path "${darkfieldPath}" \
            --mid-chunk-size "${params.unmixMidChunkSize}" \
            --downsample "${params.unmixDownsample}" \
            --dark-dir "${darkDir}" \
            --scales-shifts-dir "${scalesShiftsDir}" \
            --ref-channel "${params.refChannelIndex}" \
            --dst "unmixing-mosaic-${round}.tiff" \
            --dask-report-filename "make-unmixing-mosaic-${round}.dask-performance.html" \
            --memory-limit "${task.memory}" \
            --n-cpus "${task.cpus}"
        """

    stub:
        """
        touch "unmixing-mosaic-${round}.tiff"
        touch "make-unmixing-mosaic-${round}.dask-performance.html"
        """
}

process ASSESS_ILLUM_PROFILES_BY_ROUND {
    if (!workflow.stubRun) {
        conda "./envs/before-annotate-env.yml"
    }
    tag "round: ${round}"

    publishDir(
        path: "${params.logDir}/illum-profiles/",
        enabled: !workflow.stubRun,
        mode: "copy",
        pattern: "plot-illum-profiles-*.svg",
    )

    input:
        tuple \
            val(round), \
            path(tilesPath), \
            path(flatfieldPath), \
            path(darkfieldPath)

    output:
        path "plot-illum-profiles-${round}.svg"

    script:
        def darkDir = Paths.get(params.calibrationDir).resolve("dark")
        """
        assess-illum-profiles \
            --round-name "${round}" \
            --tiles-path "${tilesPath}" \
            --n-tiles "${params.nAssessIllum}" \
            --flatfield-path "${flatfieldPath}" \
            --darkfield-path "${darkfieldPath}" \
            --dark-dir "${darkDir}" \
            --dst "plot-illum-profiles-${round}.svg"
        """

    stub:
        """
        touch "plot-illum-profiles-${round}.svg"
        """
}

def doComputeIllumProfiles(Path illumDir, String round) {
    def flatfieldExists = illumDir.resolve("flatfield-${round}.tiff").toFile().exists()
    def darkfieldExists = illumDir.resolve("darkfield-${round}.tiff").toFile().exists()
    return !(flatfieldExists && darkfieldExists)
}

def doComputeUnmixMosaic(Path unmixDir, String round) {
    def mosaicExists = unmixDir.resolve("unmixing-mosaic-${round}.tiff").toFile().exists()
    return !mosaicExists
}

workflow PREPARE_ROUNDS {
    /*
    This module takes as argument a timestamps channel so that it runs after the cube
    alignment step.
    */

    take:
        slide
        cubeAlignmentTimestamps

    main:
        /*
        Initially we divide rounds into those that need illumination profiles computed
        and those that don't
         */
        channel.fromList(slide.getRoundNames()).set { roundsCh }

        // ILLUMINATION ================================================================
        // personally, if I rewrote this if-else block using boolean expressions it'd be confusing
        roundsCh
            .branch {
                compute: params.overwriteIllumProfiles || doComputeIllumProfiles(slide.illumDir, it)
                skip: !params.overwriteIllumProfiles
            }
            .set { illumRoundsCh }

        // compute for rounds with non-existent illum profiles
        GET_RANDOM_ILLUM_TILES_BY_ROUND(slide, illumRoundsCh.compute)
        MAKE_ILLUM_PROFILES_BY_ROUND(GET_RANDOM_ILLUM_TILES_BY_ROUND.out, slide.illumDir)

        // skip for rounds with existing illum profiles
        illumRoundsCh.skip
            .map { [
                it,
                slide.illumDir.resolve("flatfield-${it}.tiff"),
                slide.illumDir.resolve("darkfield-${it}.tiff")
            ] }
            .set { existingIllumProfilesCh }

        // concatenate all illum profiles
        MAKE_ILLUM_PROFILES_BY_ROUND.out.profiles
            .concat(existingIllumProfilesCh)
            .set { illumProfilesCh }

        // assess illumination
        GET_ALL_ILLUM_TILES_BY_ROUND(slide, roundsCh)
        GET_ALL_ILLUM_TILES_BY_ROUND.out
            .join(illumProfilesCh, by: 0)
            .map {[
                round: it[0],
                tilePaths: it[1],
                flatfieldPath: it[2],
                darkfieldPath: it[3]
            ]}
            .set { assessIllumProfilesCh }
        ASSESS_ILLUM_PROFILES_BY_ROUND(assessIllumProfilesCh)

        // UNMIXING ====================================================================
        roundsCh
            .branch {
                compute: params.overwriteUnmixingMosaic || doComputeUnmixMosaic(slide.unmixDir, it)
                skip: !params.overwriteUnmixingMosaic
            }
            .set { unmixRoundsCh }

        // compute for rounds with non-existent unmixing mosaics
        GET_UNMIXING_TILES_BY_ROUND(slide, unmixRoundsCh.compute)
        illumProfilesCh
            .join(GET_UNMIXING_TILES_BY_ROUND.out, by: 0)
            .map { [
                round: it[0],
                flatfieldPath: it[1],
                darkfieldPath: it[2],
                tilesPath: it[3],
            ] }
            .set { unmixTilesByRound }

        MAKE_UNMIXING_MOSAIC_BY_ROUND(unmixTilesByRound, slide.unmixDir)

    emit:
        illumProfilesByRound = illumProfilesCh
}