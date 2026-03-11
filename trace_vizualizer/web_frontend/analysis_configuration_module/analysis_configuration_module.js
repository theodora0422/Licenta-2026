function getAnalysisConfiguration() {
    return {
        check_deadlock: document.getElementById("deadlock").checked,
        check_data_race: document.getElementById("data-race").checked,
        check_starvation: document.getElementById("starvation").checked,
        check_mutual_exclusion: document.getElementById("mutual-exclusion").checked,
        max_depth: 10
    };
}

window.AnalysisConfigurationModule = {
    getAnalysisConfiguration
};