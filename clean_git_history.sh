#!/bin/bash

# Advanced script to completely remove large files from Git history
# WARNING: This rewrites Git history and should be used with caution

echo "=== Git History Cleanup Script ==="
echo "WARNING: This script will rewrite Git history!"
echo "Make sure you have backups and coordinate with team members."
echo ""

# Check if we're in a git repository
if [ ! -d .git ]; then
    echo "Error: Not in a Git repository"
    exit 1
fi

# List of large files to remove from history
LARGE_FILES=(
    "dearpygui_gui_examples/Image-Processing-Node-Editor/node/deep_learning_node/monocular_depth_estimation/FSRE_Depth/fsre_depth_192x320/fsre_depth_full_192x320.onnx"
    "dearpygui_gui_examples/Image-Processing-Node-Editor/node/deep_learning_node/monocular_depth_estimation/FSRE_Depth/fsre_depth_384x640/fsre_depth_full_384x640.onnx"
    "dearpygui_gui_examples/Image-Processing-Node-Editor/node/deep_learning_node/monocular_depth_estimation/HR_Depth/saved_model_hr_depth_384x1280/hr_depth_k_m_depth_encoder_depth_384x1280.onnx"
)

echo "Files to remove from history:"
for file in "${LARGE_FILES[@]}"; do
    echo "  - $file"
done

echo ""
echo "Choose cleanup method:"
echo "1) Use git filter-branch (built-in, slower)"
echo "2) Use BFG Repo-Cleaner (faster, requires installation)"
echo "3) Exit without changes"
read -p "Enter choice (1-3): " choice

case $choice in
    1)
        echo "Using git filter-branch..."

        # Create a backup branch first
        echo "Creating backup branch..."
        git branch backup-before-cleanup

        # Remove each large file from history
        for file in "${LARGE_FILES[@]}"; do
            echo "Removing $file from history..."
            git filter-branch --force --index-filter \
                "git rm --cached --ignore-unmatch '$file'" \
                --prune-empty --tag-name-filter cat -- --all
        done

        # Clean up refs
        git for-each-ref --format='delete %(refname)' refs/original | git update-ref --stdin
        git reflog expire --expire=now --all
        git gc --prune=now --aggressive

        echo "History cleanup completed with git filter-branch"
        ;;

    2)
        echo "Using BFG Repo-Cleaner..."

        # Check if BFG is installed
        if ! command -v bfg &> /dev/null; then
            echo "BFG Repo-Cleaner not found. Installing..."
            echo "Please install BFG manually:"
            echo "1. Download from: https://rtyley.github.io/bfg-repo-cleaner/"
            echo "2. Or install via package manager"
            echo "3. Then run this script again"
            exit 1
        fi

        # Create a backup branch
        echo "Creating backup branch..."
        git branch backup-before-cleanup

        # Use BFG to remove large files
        echo "Running BFG cleanup..."
        bfg --delete-files "*.onnx" .

        # Clean up
        git reflog expire --expire=now --all
        git gc --prune=now --aggressive

        echo "History cleanup completed with BFG"
        ;;

    3)
        echo "Exiting without changes"
        exit 0
        ;;

    *)
        echo "Invalid choice. Exiting."
        exit 1
        ;;
esac

echo ""
echo "=== Post-cleanup steps ==="
echo "1. Verify the cleanup worked:"
echo "   git log --oneline --all"
echo ""
echo "2. Check repository size:"
echo "   du -sh .git"
echo ""
echo "3. Force push to remote (WARNING: This rewrites remote history):"
echo "   git push --force-with-lease origin HEAD"
echo ""
echo "4. Notify team members to re-clone the repository"
echo ""
echo "5. If you need the large files, consider using Git LFS:"
echo "   git lfs track '*.onnx'"
echo "   git add .gitattributes"
echo "   git commit -m 'Add LFS tracking for ONNX files'"

echo ""
echo "=== Current repository status ==="
git status
