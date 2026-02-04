# Deploy Legal Document Agent to Azure
# This script automates the deployment using Azure Developer CLI

Write-Host "🚀 Legal Document Agent - Azure Deployment" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# Check if azd is installed
if (!(Get-Command azd -ErrorAction SilentlyContinue)) {
    Write-Host "❌ Azure Developer CLI (azd) is not installed" -ForegroundColor Red
    Write-Host "Install it from: https://aka.ms/install-azd" -ForegroundColor Yellow
    exit 1
}

# Check if user is logged in
Write-Host "🔐 Checking Azure authentication..." -ForegroundColor Yellow
azd auth login --check-status 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "Please login to Azure..." -ForegroundColor Yellow
    azd auth login
}

Write-Host "✅ Authentication verified" -ForegroundColor Green
Write-Host ""

# Get or create environment
Write-Host "📋 Environment Setup" -ForegroundColor Yellow
Write-Host "-------------------" -ForegroundColor Yellow

$envName = Read-Host "Enter environment name (e.g., legal-agent-dev)"
if ([string]::IsNullOrWhiteSpace($envName)) {
    $envName = "legal-agent-dev"
}

# Check if environment exists
$envExists = azd env list | Select-String $envName
if ($envExists) {
    Write-Host "Environment '$envName' exists. Using it..." -ForegroundColor Green
    azd env select $envName
} else {
    Write-Host "Creating new environment '$envName'..." -ForegroundColor Yellow
    azd env new $envName
}

Write-Host ""

# Get Microsoft Foundry details
Write-Host "🤖 Microsoft Foundry Configuration" -ForegroundColor Yellow
Write-Host "-----------------------------------" -ForegroundColor Yellow
Write-Host "You need a Microsoft Foundry project with a deployed model." -ForegroundColor Cyan
Write-Host "Visit https://ai.azure.com to create one." -ForegroundColor Cyan
Write-Host ""

$foundryEndpoint = Read-Host "Enter your Foundry project endpoint (e.g., https://your-project.api.azureml.ms)"
if ([string]::IsNullOrWhiteSpace($foundryEndpoint)) {
    Write-Host "⚠️  Warning: Foundry endpoint not provided. You'll need to set it later." -ForegroundColor Yellow
} else {
    azd env set FOUNDRY_ENDPOINT $foundryEndpoint
    Write-Host "✅ Foundry endpoint set" -ForegroundColor Green
}

$modelDeployment = Read-Host "Enter your model deployment name (default: gpt-5)"
if ([string]::IsNullOrWhiteSpace($modelDeployment)) {
    $modelDeployment = "gpt-5"
}
azd env set FOUNDRY_MODEL_DEPLOYMENT $modelDeployment
Write-Host "✅ Model deployment set to: $modelDeployment" -ForegroundColor Green
Write-Host ""

# Choose deployment option
Write-Host "🎯 Deployment Options" -ForegroundColor Yellow
Write-Host "---------------------" -ForegroundColor Yellow
Write-Host "1. Full deployment (provision + deploy)" -ForegroundColor White
Write-Host "2. Provision infrastructure only" -ForegroundColor White
Write-Host "3. Deploy application only (infrastructure must exist)" -ForegroundColor White
Write-Host ""

$choice = Read-Host "Select option (1-3, default: 1)"
if ([string]::IsNullOrWhiteSpace($choice)) {
    $choice = "1"
}

Write-Host ""
Write-Host "🚀 Starting deployment..." -ForegroundColor Cyan
Write-Host ""

switch ($choice) {
    "1" {
        Write-Host "Running full deployment (provision + deploy)..." -ForegroundColor Yellow
        azd up
    }
    "2" {
        Write-Host "Provisioning Azure resources..." -ForegroundColor Yellow
        azd provision
    }
    "3" {
        Write-Host "Deploying application..." -ForegroundColor Yellow
        azd deploy
    }
    default {
        Write-Host "Invalid option. Running full deployment..." -ForegroundColor Yellow
        azd up
    }
}

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "✅ Deployment completed successfully!" -ForegroundColor Green
    Write-Host ""
    Write-Host "📊 Resource Details:" -ForegroundColor Cyan
    Write-Host "-------------------" -ForegroundColor Cyan
    
    # Display resource information
    $appUrl = azd env get-value AZURE_CONTAINER_APP_URL
    $searchEndpoint = azd env get-value AZURE_SEARCH_ENDPOINT
    $docIntelEndpoint = azd env get-value AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT
    $kvName = azd env get-value AZURE_KEYVAULT_NAME
    
    Write-Host "🌐 Application URL: " -NoNewline -ForegroundColor White
    Write-Host $appUrl -ForegroundColor Cyan
    Write-Host "🔍 Search Endpoint: " -NoNewline -ForegroundColor White
    Write-Host $searchEndpoint -ForegroundColor Cyan
    Write-Host "📄 Doc Intelligence: " -NoNewline -ForegroundColor White
    Write-Host $docIntelEndpoint -ForegroundColor Cyan
    Write-Host "🔐 Key Vault: " -NoNewline -ForegroundColor White
    Write-Host $kvName -ForegroundColor Cyan
    
    Write-Host ""
    Write-Host "📝 Next Steps:" -ForegroundColor Yellow
    Write-Host "1. Create search index using 'search-index-schema.json'" -ForegroundColor White
    Write-Host "2. Upload legal documents to Azure AI Search" -ForegroundColor White
    Write-Host "3. Test the application at: $appUrl" -ForegroundColor White
    Write-Host "4. Monitor logs: azd monitor" -ForegroundColor White
    Write-Host ""
    Write-Host "📚 For more information, see AZD_DEPLOYMENT.md" -ForegroundColor Cyan
    
} else {
    Write-Host ""
    Write-Host "❌ Deployment failed. Check the errors above." -ForegroundColor Red
    Write-Host ""
    Write-Host "💡 Troubleshooting tips:" -ForegroundColor Yellow
    Write-Host "- Run with --debug flag: azd up --debug" -ForegroundColor White
    Write-Host "- Check Azure Portal for specific errors" -ForegroundColor White
    Write-Host "- Verify your Foundry endpoint is correct" -ForegroundColor White
    Write-Host "- Ensure you have necessary permissions" -ForegroundColor White
}

Write-Host ""
Write-Host "Press any key to exit..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
