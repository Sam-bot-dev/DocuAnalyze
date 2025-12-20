document.addEventListener("DOMContentLoaded", () => {
    loadDiscrepancies();
});

async function loadDiscrepancies() {
    const grid = document.getElementById("issue-grid");
    const title = document.getElementById("issue-title");
    const subtitle = document.getElementById("issue-subtitle");
    const filterBar = document.getElementById("filter-bar");
    const minimapContainer = document.getElementById("minimap-container");

    // Show loader
    grid.innerHTML = `
        <div class="col-span-full flex justify-center py-20">
            <div class="h-10 w-10 border-4 border-primary border-t-transparent rounded-full animate-spin"></div>
        </div>
    `;

    try {
        const res = await fetch("/api/discrepancy");  // ✅ CORRECT ROUTE

        if (!res.ok) throw new Error("Bad response");

        const data = await res.json();

        // ===================
        // SET PAGE HEADERS
        // ===================
        title.textContent = `We found ${data.total} issues!`;
        subtitle.textContent = `Detected in ${data.document}`;

        // ===================
        // FILTER CHIPS
        // ===================
        filterBar.innerHTML = `
            <button class="chip-active">All</button>
            <button class="chip">High</button>
            <button class="chip">Medium</button>
            <button class="chip">Low</button>
        `;

        // ===================
        // ISSUES GRID
        // ===================
        grid.innerHTML = "";

        data.issues.forEach((issue, index) => {
            grid.innerHTML += `
                <div class="issue-card">
                    <h3>${issue.title}</h3>
                    <span class="badge badge-${issue.severity}">${issue.severity}</span>

                    <p class="issue-text"><strong>Original:</strong> ${issue.original}</p>
                    <p class="issue-text"><strong>Suggested:</strong> ${issue.suggested}</p>

                    <div class="mt-3 text-xs text-gray-500">Page: ${issue.page}</div>
                </div>
            `;
        });

        // ===================
        // MINIMAP (One-page demo)
        // ===================
        minimapContainer.innerHTML = `
            <div class="minimap-page relative bg-white dark:bg-slate-800 rounded border shadow-sm p-4"
                 style="height:500px">
                ${data.issues.map(i => `
                    <div class="minimap-issue-marker"
                         style="
                            top:${i.bbox[1] * 100}%;
                            left:${i.bbox[0] * 100}%;
                         ">
                    </div>
                `).join("")}
            </div>
        `;

    } catch (err) {
        grid.innerHTML = `
            <div class="col-span-full text-center text-red-500 py-10 font-medium">
                Could not load issues.
            </div>
        `;
    }
}
