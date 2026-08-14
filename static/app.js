function toggleSidebar() {
    document.getElementById("sidebar").classList.toggle("open");
}

document.addEventListener("click", function (event) {
    const sidebar = document.getElementById("sidebar");
    const menuButton = document.querySelector(".menu-button");
    if (!sidebar || !sidebar.classList.contains("open")) return;
    if (!sidebar.contains(event.target) && !menuButton.contains(event.target)) {
        sidebar.classList.remove("open");
    }
});
