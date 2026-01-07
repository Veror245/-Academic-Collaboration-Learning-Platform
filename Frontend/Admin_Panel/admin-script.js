const API_BASE_URL = "http://127.0.0.1:8000";

// Rooms to scan
const ROOM_SLUGS = ["cs", "ece", "mech", "civil", "science", "hum"];

function getAuthToken() {
    return localStorage.getItem("access_token");
}

// MAIN FUNCTION: Fetch and Load Resources
async function loadResources() {
    const tableBody = document.getElementById("resource-table-body");
    const countLabel = document.getElementById("total-count"); // Get the stat number element
    const token = getAuthToken();

    if (!token) {
        window.location.href = "/Frontend/Admin_login/adminLogin.html";
        return;
    }

    try {
        tableBody.innerHTML = `<tr><td colspan="5" style="text-align:center; padding: 20px; color: #666;">Scanning all rooms...</td></tr>`;

        // Parallel Fetch
        const fetchPromises = ROOM_SLUGS.map(slug =>
            fetch(`${API_BASE_URL}/student/room/${slug}/resources`, {
                method: "GET",
                headers: { "Authorization": `Bearer ${token}` }
            })
                .then(res => res.ok ? res.json() : [])
                .catch(err => [])
        );

        const results = await Promise.all(fetchPromises);
        const allResources = results.flat();

        // Sort: Newest first
        allResources.sort((a, b) => b.id - a.id);

        // --- INTERACTIVE UPDATE ---
        // Update the dashboard number
        if (countLabel) {
            countLabel.textContent = allResources.length;
        }

        tableBody.innerHTML = "";

        if (allResources.length === 0) {
            tableBody.innerHTML = `<tr><td colspan="5" style="text-align:center; padding: 20px;">No uploads found.</td></tr>`;
            return;
        }

        // Render rows
        allResources.forEach(resource => {
            const isVerified = resource.is_verified || false;
            const statusClass = isVerified ? "status-approved" : "status-pending";
            const statusText = isVerified ? "Verified" : "Pending";

            // Uploader Name Logic
            let uploaderName = "Unknown";
            if (resource.uploader) {
                uploaderName = resource.uploader;
            } else if (resource.user && resource.user.username) {
                uploaderName = resource.user.username;
            }

            const row = `
                <tr id="row-${resource.id}">
                    <td>
                        <div style="font-weight:600; font-size: 0.95rem;">${resource.title || "Untitled"}</div>
                        <div style="font-size:0.8rem; margin-top:4px;">
                            <a href="${API_BASE_URL}/${resource.file_path}" target="_blank" style="color:#3b82f6; text-decoration:none; background:#f1f5f9; padding:2px 6px; border-radius:4px;">View PDF</a>
                        </div>
                    </td>
                    <td>
                        <div style="font-weight:500; color:#334155;">${uploaderName}</div>
                    </td>
                    <td>PDF</td>
                    <td><span class="${statusClass}" id="status-${resource.id}">${statusText}</span></td>
                    <td>
                        <button class="btn btn-reject" style="background-color: #ef4444; color: white; padding: 6px 14px; border-radius:6px; border:none; cursor:pointer; font-weight:500; transition: background 0.2s;" onclick="deleteResource(${resource.id})">Delete</button>
                    </td>
                </tr>
            `;
            tableBody.innerHTML += row;
        });

    } catch (error) {
        console.error("Global Error:", error);
        tableBody.innerHTML = `<tr><td colspan="5" style="text-align:center; color:red;">Error loading data.</td></tr>`;
    }
}

// ACTION: Delete Resource
async function deleteResource(resourceId) {
    if (!confirm("Are you sure you want to permanently delete this file?")) return;

    const token = getAuthToken();
    try {
        const response = await fetch(`${API_BASE_URL}/admin/delete-resource/${resourceId}`, {
            method: "DELETE",
            headers: {
                "Authorization": `Bearer ${token}`
            }
        });

        if (response.ok) {
            const row = document.getElementById(`row-${resourceId}`);

            // Visual removal
            row.style.opacity = "0";
            setTimeout(() => row.remove(), 500);

            // Update the counter immediately
            const countLabel = document.getElementById("total-count");
            if (countLabel) {
                countLabel.textContent = parseInt(countLabel.textContent) - 1;
            }
        } else {
            const err = await response.json();
            alert("Error: " + err.detail);
        }
    } catch (error) {
        alert("Server connection error.");
    }
}

document.addEventListener("DOMContentLoaded", loadResources);