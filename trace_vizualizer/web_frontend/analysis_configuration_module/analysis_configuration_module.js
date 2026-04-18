function getSelectedProperty() {
    const selectedOption = document.querySelector('input[name="analysis-property"]:checked');

    if (!selectedOption) {
        return null;
    }

    return selectedOption.value;
}

function getAnalysisConfiguration() {
    const selectedProperty = getSelectedProperty();

    return {
        check_deadlock: selectedProperty === "deadlock",
        check_starvation: selectedProperty === "starvation",
        check_data_race: selectedProperty === "data_race",
        check_mutual_exclusion: selectedProperty === "mutual_exclusion"
    };
}

window.AnalysisConfigurationModule = {
    getAnalysisConfiguration
};