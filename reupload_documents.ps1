# Script to re-upload documents to ensure full content extraction
# This will delete existing documents and re-upload them

$appUrl = "https://ca-7alsezpsk27uq.eastus2.azurecontainerapps.io"

Write-Host "===== Legal Document Re-upload Script =====" -ForegroundColor Cyan
Write-Host ""

# Get list of current documents
Write-Host "Fetching current documents..." -ForegroundColor Yellow
try {
    $documents = Invoke-RestMethod -Uri "$appUrl/api/documents" -Method Get
    Write-Host "Found $($documents.Count) documents" -ForegroundColor Green
    
    # Display documents
    foreach ($doc in $documents) {
        Write-Host "  - $($doc.title) (ID: $($doc.id), Length: $($doc.content_length) chars)" -ForegroundColor Gray
    }
    Write-Host ""
    
    # Ask for confirmation to delete
    $confirm = Read-Host "Do you want to delete all documents and re-upload? (yes/no)"
    if ($confirm -ne "yes") {
        Write-Host "Operation cancelled" -ForegroundColor Red
        exit
    }
    
    # Delete each document
    Write-Host "Deleting documents..." -ForegroundColor Yellow
    foreach ($doc in $documents) {
        try {
            Invoke-RestMethod -Uri "$appUrl/api/documents/$($doc.id)" -Method Delete | Out-Null
            Write-Host "  ✓ Deleted: $($doc.title)" -ForegroundColor Green
        } catch {
            Write-Host "  ✗ Failed to delete: $($doc.title) - $($_.Exception.Message)" -ForegroundColor Red
        }
    }
    Write-Host ""
    
    # Check for PDF files in current directory
    $pdfFiles = Get-ChildItem -Path . -Filter *.pdf
    
    if ($pdfFiles.Count -eq 0) {
        Write-Host "No PDF files found in current directory" -ForegroundColor Red
        Write-Host "Please place your PDF files here and run the script again" -ForegroundColor Yellow
        exit
    }
    
    Write-Host "Found $($pdfFiles.Count) PDF files to upload:" -ForegroundColor Yellow
    foreach ($file in $pdfFiles) {
        Write-Host "  - $($file.Name)" -ForegroundColor Gray
    }
    Write-Host ""
    
    $confirmUpload = Read-Host "Upload these files? (yes/no)"
    if ($confirmUpload -ne "yes") {
        Write-Host "Upload cancelled" -ForegroundColor Red
        exit
    }
    
    # Upload each file
    Write-Host "Uploading documents..." -ForegroundColor Yellow
    foreach ($file in $pdfFiles) {
        try {
            $fileBytes = [System.IO.File]::ReadAllBytes($file.FullName)
            $fileContent = [System.Net.Http.ByteArrayContent]::new($fileBytes)
            $fileContent.Headers.ContentType = [System.Net.Http.Headers.MediaTypeHeaderValue]::Parse("application/pdf")
            
            $multipart = [System.Net.Http.MultipartFormDataContent]::new()
            $multipart.Add($fileContent, "file", $file.Name)
            
            $httpClient = [System.Net.Http.HttpClient]::new()
            $response = $httpClient.PostAsync("$appUrl/api/upload", $multipart).Result
            $result = $response.Content.ReadAsStringAsync().Result | ConvertFrom-Json
            
            if ($result.status -eq "success") {
                Write-Host "  ✓ Uploaded: $($file.Name) - Extracted $($result.extracted_length) chars using $($result.extraction_method)" -ForegroundColor Green
                if ($result.extracted_length -lt 1000) {
                    Write-Host "    ⚠ Warning: Short extraction - only $($result.extracted_length) characters" -ForegroundColor Yellow
                }
            } else {
                Write-Host "  ✗ Failed: $($file.Name) - $($result.message)" -ForegroundColor Red
            }
        } catch {
            Write-Host "  ✗ Error uploading $($file.Name): $($_.Exception.Message)" -ForegroundColor Red
        }
    }
    
    Write-Host ""
    Write-Host "===== Upload Complete =====" -ForegroundColor Cyan
    Write-Host "You can now test your queries in the chat interface" -ForegroundColor Green
    
} catch {
    Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Red
}
