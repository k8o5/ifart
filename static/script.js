document.addEventListener('DOMContentLoaded', () => {
    // Get the modal
    const modal = document.getElementById("taskModal");

    // Get the button that opens the modal
    const btn = document.getElementById("openModalBtn");

    // Get the <span> element that closes the modal
    const span = document.getElementsByClassName("close-btn")[0];

    // Get the submit button
    const submitBtn = document.getElementById("submitTaskBtn");

    // Get the task input
    const taskInput = document.getElementById("taskInput");

    // When the user clicks the button, open the modal
    btn.onclick = function() {
        modal.style.display = "block";
    }

    // When the user clicks on <span> (x), close the modal
    span.onclick = function() {
        modal.style.display = "none";
    }

    // When the user clicks anywhere outside of the modal, close it
    window.onclick = function(event) {
        if (event.target == modal) {
            modal.style.display = "none";
        }
    }

    // When the user clicks the submit button
    submitBtn.onclick = function() {
        const task = taskInput.value.trim();
        if (task) {
            console.log("Sending task to agent launcher:", task);

            fetch('/agent', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ task: task }),
            })
            .then(response => response.json())
            .then(data => {
                console.log('Server response:', data);
                // Optionally, give user feedback here
                alert(`Agent for task "${task}" launched!`);
            })
            .catch((error) => {
                console.error('Error:', error);
                alert('Failed to launch agent. Check console for details.');
            });

            taskInput.value = ""; // Clear the input field
            // Maybe don't close the modal, so the user can fire off multiple agents
            // modal.style.display = "none";
        } else {
            alert("Please enter a task! uwu");
        }
    }
});
