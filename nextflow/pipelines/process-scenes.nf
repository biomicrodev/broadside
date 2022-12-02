import java.nio.file.Paths

params.refChannelIndex = 0
params.ashlarMaxShiftUM = 50
params.ashlarFilterSigma = 3
params.ashlarTileSize = 2048

def newline = "\n"
def colSep = "\t"

process COLLECT_TILES_BY_SCENE_ROUND {
    tag "scene: ${scene}, round: ${round}"

    input:
        val slide
        tuple \
            val(scene), \
            val(round)

    output:
        tuple \
            val(scene), \
            val(round), \
            path("tiles-${scene}-${round}.txt")

    exec:
        def tilePaths = slide.getScene(scene).getTilePathsForRound(round)
        def dst = task.workDir.resolve("tiles-${scene}-${round}.txt")
        file(dst).text = tilePaths.join(newline)
}

process STACK_TILES_BY_SCENE_ROUND {
    if (!workflow.stubRun) {
        conda "./envs/before-annotate-env.yml"
    }
    tag "scene: ${scene}, round: ${round}"
    memory "8 GB"
    cpus 2

    publishDir(
        path: "${params.logDir}/stack-tiles/",
        enabled: !workflow.stubRun,
        mode: "copy",
        pattern: "stack-tiles-*.dask-performance.html",
    )

    input:
        tuple \
            val(scene), \
            val(round), \
            path(flatfieldPath), \
            path(darkfieldPath), \
            path(tilesPath)

    output:
        tuple \
            val(scene), \
            val(round), \
            path(tilesPath), \
            path("stack-${scene}-${round}.ome.tiff"), emit: stacks
        path("stack-tiles-${scene}-${round}.dask-performance.html")

    script:
        def darkDir = Paths.get(params.calibrationDir).resolve("dark")
        def scalesShiftsDir = Paths.get(params.calibrationDir).resolve("cube-alignment").resolve("scales-shifts")
        """
        stack-tiles \
            --tiles-path "${tilesPath}" \
            --flatfield-path "${flatfieldPath}" \
            --darkfield-path "${darkfieldPath}" \
            --dark-dir "${darkDir}" \
            --scales-shifts-dir "${scalesShiftsDir}" \
            --dst "stack-${scene}-${round}.ome.tiff" \
            --dask-report-filename "stack-tiles-${scene}-${round}.dask-performance.html" \
            --n-cpus "${task.cpus}" \
            --memory-limit "${task.memory}"
        """

    stub:
        """
        touch "stack-${scene}-${round}.ome.tiff"
        touch "stack-tiles-${scene}-${round}.dask-performance.html"
        """
}

process SORT_STACKS {
    // needed so that the cycles for each scene are in order
    tag "scene: ${scene}"

    input:
        tuple \
            val(scene), \
            val(rounds), \
            val(tilesPaths), \
            val(stackPaths)

    output:
        tuple \
            val(scene), \
            val(roundsSorted), \
            val(tilesPathsSorted), \
            val(stackPathsSorted)

    exec:
        /*
        This is really ugly; preferably we would like to sort all three lists using the
        first list as a key, but I can't be bothered to make it more complicated than it
        really is
        */
        roundsSorted = rounds.sort({ a, b -> a <=> b})
        tilesPathsSorted = tilesPaths.sort({ a, b -> a.name <=> b.name})
        stackPathsSorted = stackPaths.sort({ a, b -> a.name <=> b.name})
}

process COLLECT_STACKS_BY_SCENE {
    tag "scene: ${scene}"
    input:
        tuple val(scene), val(stackPaths)

    output:
        tuple val(scene), path("stacks-${scene}.txt")

    exec:
        def dst = task.workDir.resolve("stacks-${scene}.txt")
        file(dst).text = stackPaths.join(newline)
}

process COLLECT_TILES_BY_SCENE {
    tag "scene: ${scene}"

    input:
        tuple \
            val(scene), \
            val(rounds), \
            val(tilesPaths)

    output:
        tuple val(scene), path("tiles-by-round-${scene}.tsv")

    exec:
        def lines = [["round", "tiles-path"].join(colSep)]
        def roundsPaths = [rounds, tilesPaths].transpose()
        roundsPaths = roundsPaths.sort({a, b -> a[0] <=> b[0]})
        for (roundPath in roundsPaths) {
            lines.add(roundPath.join(colSep))
        }
        def dst = task.workDir.resolve("tiles-by-round-${scene}.tsv")
        file(dst).text = lines.join(newline)
}

process REGISTER_AND_STITCH_SCENE {
    if (!workflow.stubRun) {
        conda "./envs/before-annotate-env.yml"
    }
    tag "scene: ${sceneName}"

    publishDir(
        path: "${omeTiffDir}",
        mode: "move",
        enabled: !workflow.stubRun,
    )

    input:
        val slideName
        tuple \
            val(sceneName), \
            val(omeTiffDir), \
            path(stacksPath), \
            path(tilesPath)

    output:
        path "${params.omeTiffFilename}"

    script:
        def omeImageName = "{\\\"slide\\\": \\\"${slideName}\\\", \\\"scene\\\": \\\"${sceneName}\\\"}"
        """
        register-and-stitch \
            --output "${params.omeTiffFilename}" \
            --stacks-path "${stacksPath}" \
            --align-channel "${params.refChannelIndex}" \
            --filter-sigma "${params.ashlarFilterSigma}" \
            --maximum-shift "${params.ashlarMaxShiftUM}" \
            --tile-size "${params.ashlarTileSize}"

        write-ome-metadata \
            --stacks-path "${stacksPath}" \
            --tiles-path "${tilesPath}" \
            --dst "${params.omeTiffFilename}" \
            --ome-image-name "${omeImageName}"
        """

    stub:
        """
        touch "${params.omeTiffFilename}"
        """
}

workflow PROCESS_SCENES {
    take:
        slide
        illumProfilesByRound

    main:
        /*
        This way of mapping is unnecessary but lets the programmer know what to expect.
        It won't run if they are switched, but still...
        */
        channel.fromList(slide.getSceneNames()).set { scenesCh }

        scenesCh
            .map { [it, slide.getScene(it).getRoundNames()] }
            .transpose()
            .map { [scene: it[0], round: it[1]] }
            .map { [it.scene, it.round] }
            .set { scenesRoundsCh }
        COLLECT_TILES_BY_SCENE_ROUND(slide, scenesRoundsCh)

        scenesCh
            .combine(illumProfilesByRound)
            .map { [scene: it[0], round: it[1], flatfield: it[2], darkfield: it[3]] }
            .filter { slide.getScene(it.scene).getRoundNames().contains(it.round) }
            .map { [it.scene, it.round, it.flatfield, it.darkfield] }
            .join(COLLECT_TILES_BY_SCENE_ROUND.out, by: [0, 1])
            .set { scenesRoundsPropsCh }
        STACK_TILES_BY_SCENE_ROUND(scenesRoundsPropsCh)
        SORT_STACKS(STACK_TILES_BY_SCENE_ROUND.out.stacks.groupTuple())
        SORT_STACKS.out
            .map { [
                scene: it[0],
                rounds: it[1],
                tilesPaths: it[2],
                stackPaths: it[3],
            ] }
            .set { roundPropsBySceneCh }

        roundPropsBySceneCh
            .map { [scene: it.scene, stackPaths: it.stackPaths] }
            .set { scenesStackPathsCh }
        COLLECT_STACKS_BY_SCENE(scenesStackPathsCh)

        roundPropsBySceneCh
            .map { [scene: it.scene, rounds: it.rounds, tilesPaths: it.tilesPaths ]}
            .set { scenesRoundsTilesPathsCh }
        COLLECT_TILES_BY_SCENE(scenesRoundsTilesPathsCh)

        scenesCh
            .map { [it, slide.getScene(it).path] }
            .join(COLLECT_STACKS_BY_SCENE.out, by: 0)
            .join(COLLECT_TILES_BY_SCENE.out, by: 0)
            .map { [
                scene: it[0],
                omeTiffDir: it[1],
                stacksPath: it[2],
                tilesPath: it[3]
            ] }
            .set { sceneStacksPathTilesPathCh }
        REGISTER_AND_STITCH_SCENE(slide.name, sceneStacksPathTilesPathCh)
}
