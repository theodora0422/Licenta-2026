async function analyzeCode(){
    const codeInput=document.getElementById("code-input");
    const resultsContainer=document.getElementById("results");

    const requestBody={
        source_code:codeInput.value,
        check_deadlock:document.getElementById("deadlock").checked,
        check_data_race:document.getElementById("data-race").checked,
        check_starvation:document.getElementById("starvation").checked,
        check_mutual_exclusion:document.getElementById("mutual-exclusion").checked,
        max_depth: 10
    };
    resultsContainer.textContent="Running analysis..";
    try{
        const response=await fetch("/analyze",{
            method:"POST",
            headers:{
                "Content-Type":"application/json"
            },
            body: JSON.stringify(requestBody)
        });
        if(!response.ok){
            throw new Error(`HTTP error: ${response.status}`);
        }
        const data=await response.json();

        window.renderAnalysisResults(data);
    }catch(error){
        resultsContainer.textContent=`Request failed: ${error.message}`;
        console.error("Analysis request failed:",error);
    }
}

document.addEventListener("DOMContentLoaded",()=>{
   const analyzeButton=document.getElementById("analyze-btn");
   analyzeButton.addEventListener("click",analyzeCode);
});