package broadside

import groovy.json.JsonSlurper
import groovy.util.logging.Log

import java.nio.file.Files
import java.nio.file.InvalidPathException
import java.nio.file.Path
import java.util.stream.Collectors

@Log
class Slide {
    Path path
    String name = path.getFileName().toString()
    List<String> allSceneNames
    List<Scene> scenes

    Path jsonPath = path.resolve(".slide.json")
    Path illumDir = path.resolve(".illumination")
    Path unmixDir = path.resolve(".unmixing")

    Slide(Path path, Set<String> selectedSceneNames = null, Set<String> selectedRoundNames = null) {
        this.path = path

        // validate inputs
        if (!Files.exists(path) || !Files.exists(jsonPath)) {
            throw new InvalidPathException(path.toString(), "Path is not a valid slide")
        }

        // get and validate scene names
        def sceneNamesFromJson = getSceneNamesFromJson()
        def sceneNamesFromFS = getSceneNamesFromFileSystem()
        if (sceneNamesFromJson != sceneNamesFromFS) {
            log.warning("Mismatch between scenes in slide.json and scenes on filesystem; using filesystem")
        }

        // store names of all scenes
        this.allSceneNames = sceneNamesFromFS.toList().sort()

        // create scene objects for selected scene names
        def sceneNames
        if (selectedSceneNames != null) {
            def extraNames = selectedSceneNames - sceneNamesFromFS
            if (extraNames.size() != 0) {
                log.warning("Unrecognized scene names: ${extraNames}")
            }

            sceneNames = sceneNamesFromFS.intersect(selectedSceneNames)
        } else {
            sceneNames = sceneNamesFromFS
        }
        this.scenes = sceneNames
                .stream()
                .map { new Scene(path.resolve(it), selectedRoundNames) }
                .collect(Collectors.toList())
                .sort { it.name }
    }

    private Set<String> getSceneNamesFromJson() {
        def jsonSlurper = new JsonSlurper()
        def config = jsonSlurper.parse(jsonPath.toFile())

        return config.polygons.stream().map { it.name }.collect(Collectors.toSet())
    }

    private Set<String> getSceneNamesFromFileSystem() {
        def sceneNames = [] as Set
        path.toFile().eachDir {
            def tilesPath = it.toPath().resolve("tiles")
            if (Files.exists(tilesPath)) {
                sceneNames.add(it.toPath().getFileName().toString())
            }
        }
        return sceneNames
    }

    Scene getScene(String name) {
        for (scene in scenes) {
            if (scene.name == name) {
                return scene
            }
        }
        throw new NoSuchElementException(name)
    }

    List<String> getRoundNames() {
        def roundNames = [] as Set
        for (scene in scenes) {
            roundNames.addAll(scene.roundNames)
        }
        return roundNames.toList().sort()
    }

    List<String> getSceneNames() {
        return scenes.stream().map { it.name }.collect(Collectors.toList())
    }

    String nextflowStatus() {
        def sceneNames = scenes
                .stream()
                .map { it.name }
                .collect(Collectors.toList())

        def scenesPrettified = scenes
                .stream()
                .map { it.summary() }
                .collect(Collectors.toList())
                .join('\n')

        return """\
slide:              ${name}
location:           ${path}
scenes found:       ${allSceneNames}
scenes to process:  ${sceneNames}
rounds to process:  ${getRoundNames()}

${scenesPrettified}\
"""
    }

    String detailedSummary() {
        def scenesPrettified = scenes
                .stream()
                .map { it.detailedSummary() }
                .collect(Collectors.toList())
                .join('\n\n')
        return """\
slide:    ${name}
location: ${path}
scenes:   ${allSceneNames}

${scenesPrettified}\
"""
    }

    List<Path> getTilePathsForRound(String roundName) {
        List<Path> tilePaths = []
        for (scene in scenes) {
            tilePaths.addAll(scene.getTilePathsForRound(roundName))
        }
        return tilePaths
    }
}
