function buildAnalysisRequest() {
    const sourceCode = window.CodeInputModule.getSourceCode();
    const configuration = window.AnalysisConfigurationModule.getAnalysisConfiguration();

    return {
        source_code: sourceCode,
        ...configuration
    };
}

window.RequestBuilder = {
    buildAnalysisRequest
};