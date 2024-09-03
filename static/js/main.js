document.addEventListener('DOMContentLoaded', function() {
    const inputForm = document.getElementById('input-form');
    const outputDiv = document.getElementById('output');
    const addAiForm = document.getElementById('add-ai-form');

    if (inputForm) {
        inputForm.addEventListener('submit', function(e) {
            e.preventDefault();
            const input = document.getElementById('user-input').value;
            processInput(input);
        });
    }

    if (addAiForm) {
        addAiForm.addEventListener('submit', function(e) {
            e.preventDefault();
            const formData = new FormData(this);
            const data = Object.fromEntries(formData.entries());

            fetch('/api/add_ai', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(data),
            })
            .then(response => response.json())
            .then(result => {
                alert(result.message);
                if (result.id) {
                    // Redirect to AI Manager page or clear the form
                    window.location.href = '/ai_manager';
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('An error occurred while adding the AI.');
            });
        });
    }

    function processInput(input) {
        fetch('/api/process_input', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({input: input, type: 'text'}),
        })
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                outputDiv.innerHTML = `<p class="error">${data.error}</p>`;
            } else {
                outputDiv.innerHTML = `<p>${JSON.stringify(data)}</p>`;
            }
        })
        .catch((error) => {
            console.error('Error:', error);
            outputDiv.innerHTML = `<p class="error">An error occurred while processing your request.</p>`;
        });
    }
});