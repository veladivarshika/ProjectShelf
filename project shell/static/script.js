
/* PROJECT SEARCH AND CATEGORY FILTER */

const searchInput = document.getElementById("searchInput");
const categoryFilter = document.getElementById("categoryFilter");
const cards = document.querySelectorAll(".card");

function filterProjects() {
    const searchText = searchInput.value.toLowerCase();
    const selectedCategory = categoryFilter.value;

    cards.forEach(function(card) {
        const title = card.querySelector("h3").textContent.toLowerCase();
        const category = card.querySelector("span").textContent;

        const matchesSearch = title.includes(searchText);

        const matchesCategory =
            selectedCategory === "all" ||
            category === selectedCategory;

        card.style.display =
            matchesSearch && matchesCategory ? "" : "none";
    });
}

searchInput.addEventListener("input", filterProjects);
categoryFilter.addEventListener("change", filterProjects);


/* OPEN PROJECT DETAILS PAGE */

function openProject(projectName) {
    window.location.href =
        "project-details.html?project=" +
        encodeURIComponent(projectName);
}