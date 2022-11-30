package broadside

import groovy.io.FileType
import groovy.util.logging.Log

import java.nio.file.Files
import java.nio.file.InvalidPathException
import java.nio.file.Path
import java.util.regex.Pattern
import java.util.stream.Collectors


@Log
class Scene {
    /*
    - scene1
        - tiles
            - round0
                - 0.ome.tiff
                - ...
            - round1
                - 0.ome.tiff
                - ...
    */

    Path path
    String name = path.getFileName().toString()
    List<String> allRoundNames
    List<String> roundNames

    Pattern roundPattern = ~/R.*/
    Pattern tileFilenamePattern = ~/[0-9]+\.ome\.tiff/
    Path tilesPath = path.resolve('tiles')

    Scene(Path path, Set<String> selectedRoundNames = null) {
        this.path = path

        // validate inputs
        if (!Files.exists(path) | !Files.exists(tilesPath)) {
            throw new InvalidPathException(path.toString(), "Path is not a valid scene")
        }

        // get round names
        def allRoundNames = getRoundNamesFromFileSystem()

        def roundNames
        if (selectedRoundNames != null) {
            def extraNames = selectedRoundNames - allRoundNames
            if (extraNames.size() != 0) {
                log.warning("Unrecognized round names found: ${extraNames}")
            }

            roundNames = allRoundNames.intersect(selectedRoundNames)
        } else {
            roundNames = allRoundNames
        }

        this.roundNames = roundNames.toList().sort()
        this.allRoundNames = allRoundNames.toList().sort()
    }

    private Set<String> getRoundNamesFromFileSystem() {
        def roundNames = [] as Set

        tilesPath.toFile().eachFile(FileType.DIRECTORIES) {
            def dirName = it.toPath().getFileName().toString()
            if (dirName ==~ roundPattern) {
                roundNames.add(dirName)
            }
        }

        return roundNames
    }

    String summary() {
        return "scene: ${name} (rounds found: ${allRoundNames})"
    }

    String detailedSummary() {
        def roundsSummary = ""
        for (roundName in roundNames) {
            def nImages = getTilePathsForRound(roundName).size()
            roundsSummary += "\n\t${roundName}:\t${nImages} tiles"
        }

        return "scene ${name}; rounds:${roundsSummary}"
    }

    List<Path> getTilePathsForRound(String roundName) {
        if (!getRoundNames().contains(roundName)) {
            return []
        }

        return tilesPath
                .resolve(roundName)
                .toFile()
                .listFiles()
                .toList()
                .stream()
                .map { it.toPath() }
                .filter { it.getFileName().toString() ==~ tileFilenamePattern }
                .collect(Collectors.toList())
    }
}