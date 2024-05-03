import React, { useState } from 'react';

const Data: React.FC = () => {
    const [fileUploaded, setFileUploaded] = useState<boolean>(false);
    const [imageSrc, setImageSrc] = useState<string | null>(null);

    // Function to handle file upload
    const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
        const file = event.target.files?.[0];
        if (file) {
            // Check if the uploaded file is a CSV file
            if (file.type === 'text/csv') {
                setFileUploaded(true);
                try {
                    console.log(file)
                    const response = await fetch(process.env.BACKEND_URL + "api/generate_visualization", {
                        method: "POST",
                        headers: {
                            "Content-Type": "application/json",
                        },
                        body: file,
                    });
                    console.log(response);
                    // Handle response here
                    if (response.ok) {
                        const imageData = await response.text();
                        setImageSrc(`data:image/png;base64,${imageData}`);
                    } else {
                        alert('Failed to generate visualization. Please try again.');
                    }
                } catch (error) {
                    console.error('Error uploading file:', error);
                }
            } else {
                alert('Please upload a CSV file.');
            }
        }
    };

    return (
        <div className="container mx-auto px-4 py-8 flex flex-col items-center">
            <h1 className="text-3xl font-bold mb-4">Data Visualization</h1>
            <div className="flex items-center">
                <input
                    type="file"
                    accept=".csv"
                    onChange={handleFileUpload}
                    className="p-2 border border-gray-400 rounded-lg mr-4"
                />
                {fileUploaded && <p className="text-green-500">File uploaded successfully!</p>}
            </div>
            {imageSrc && <img src={imageSrc} alt="Visualization" className="mt-4" />}
        </div>
    );
};

export default Data;