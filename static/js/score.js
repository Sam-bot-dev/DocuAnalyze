document.addEventListener("DOMContentLoaded", () => {
    loadScore();
});

async function loadScore() {
    const res = await fetch("/api/score");
    const data = await res.json();

    // Score
    document.getElementById("final-score").textContent = data.score;

    // Severity
    document.getElementById("sev-high").textContent = data.severity.high;
    document.getElementById("sev-medium").textContent = data.severity.medium;
    document.getElementById("sev-low").textContent = data.severity.low;

    // Issues table
    const table = document.getElementById("issue-table");
    table.innerHTML = "";

    data.issues.forEach(issue => {
        table.innerHTML += `
            <tr class="hover:bg-slate-50 dark:hover:bg-slate-700/30 transition-colors">
                <td class="p-4 font-semibold">${issue.category}</td>
                <td class="p-4 capitalize">${issue.severity}</td>
                <td class="p-4">${issue.description}</td>
                <td class="p-4">${issue.page}</td>
            </tr>
        `;
    });

    // Radar Chart
    const ctx = document.getElementById("scoreRadar");

    new Chart(ctx, {
        type: "radar",
        data: {
            labels: ["Tone", "Clarity", "Factual", "Typo", "Structure"],
            datasets: [{
                label: "Score Breakdown",
                data: data.breakdown,
                borderWidth: 2,
                borderColor: "#138aec",
                backgroundColor: "rgba(19, 138, 236, 0.25)"
            }]
        },
        options: {
            scales: { r: { beginAtZero: true, max: 100 } }
        }
    });
}
document.getElementById("export-btn").addEventListener("click", () => {
    window.location.href = "/api/export-pdf";
});
