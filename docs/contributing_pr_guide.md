# Guide for Submitting Changes to the CUDOS Framework

This guide walks you through the process of submitting your changes to the CUDOS Framework repository using Git and creating a Pull Request (PR).

## Prerequisites

- Git installed on your local machine
- GitHub account with access to the repository
- Local clone of the repository with your changes

## Step 1: Create a Feature Branch

Before making changes, create a feature branch to isolate your work:

```bash
# Ensure you're on the main branch and up-to-date
git checkout main
git pull origin main

# Create and checkout a new feature branch
git checkout -b feature/cost-forecast-automation
```

Branch naming conventions:
- `feature/` - for new features
- `fix/` - for bug fixes
- `docs/` - for documentation updates
- `refactor/` - for code refactoring

## Step 2: Make and Test Your Changes

1. Make your changes to the codebase
2. Test thoroughly following the testing guides
3. Ensure all tests pass and the feature works as expected

## Step 3: Stage and Commit Your Changes

```bash
# Check what files you've changed
git status

# Stage your changes
git add cfn-templates/cost-forecast-collection.yaml
git add docs/cost_forecast_automation.md
git add docs/cost_forecast_testing.md
git add README.md

# Commit your changes with a descriptive message
git commit -m "Add AWS Cost Explorer forecast automation"
```

### Writing a Good Commit Message

For larger changes, consider using a multi-line commit message:

```bash
git commit -m "Add AWS Cost Explorer forecast automation

- Add CloudFormation template for automated data collection
- Create documentation for deployment and testing
- Update main README with feature information
- Ensure integration with existing CUDOS dashboard framework"
```

## Step 4: Push Your Branch

```bash
# Push your feature branch to the remote repository
git push origin feature/cost-forecast-automation
```

## Step 5: Create a Pull Request

1. Go to the repository on GitHub
2. You should see a prompt to create a pull request for your recently pushed branch
3. Click on "Compare & pull request"

### Writing a Good PR Description

Include the following in your PR description:

```markdown
## AWS Cost Explorer Forecast Automation

This PR adds automated AWS Cost Explorer forecast data collection to the CUDOS framework.

### Changes
- Added CloudFormation template for scheduled data collection
- Created Lambda function for Cost Explorer API integration
- Set up Athena table creation for forecast data
- Added comprehensive documentation and testing guide
- Updated main README with feature information

### Testing
The changes have been tested using the procedures outlined in `docs/cost_forecast_testing.md`.

### Screenshots
[Add screenshots of the deployed dashboard if applicable]

### Checklist
- [x] Code follows project style guidelines
- [x] Documentation has been updated
- [x] All tests passing
- [x] No security issues introduced
```

## Step 6: Respond to Review Comments

After submitting your PR, reviewers may request changes or have questions:

1. Address all review comments
2. Make additional commits to address feedback
3. Push changes to the same branch
4. Respond to comments in the PR

## Step 7: Merge Your PR

Once your PR is approved:

1. Make sure your branch is up-to-date with the main branch
2. Resolve any merge conflicts if necessary
3. Follow the repository's merge strategy (merge commit, squash, or rebase)
4. Delete your branch after merging (GitHub offers this option)

## Tips for Successful PRs

1. **Keep PRs focused**: Each PR should address a single feature or fix
2. **Test thoroughly**: Ensure your changes work as expected and don't break existing functionality
3. **Update documentation**: Always update relevant documentation with your code changes
4. **Be responsive**: Respond promptly to review comments
5. **Check CI/CD**: Ensure all automated tests pass before requesting a review

## Common PR Issues

- **Large PRs**: Break down large changes into smaller, more manageable PRs
- **Merge conflicts**: Regularly rebase your branch on main to minimize conflicts
- **Missing tests**: Include tests for your changes
- **Incomplete documentation**: Ensure your changes are well-documented

## Example Git Workflow for This Feature

```bash
# Start from a clean main branch
git checkout main
git pull origin main

# Create feature branch
git checkout -b feature/cost-forecast-automation

# Make changes to files
# ... editing files ...

# Stage and commit
git add cfn-templates/cost-forecast-collection.yaml docs/cost_forecast_*.md README.md
git commit -m "Add AWS Cost Explorer forecast automation

- CloudFormation template for scheduled forecast collection
- Lambda function for Cost Explorer API integration 
- Documentation for deployment and testing
- README update with feature information"

# Push to remote
git push origin feature/cost-forecast-automation

# Create PR on GitHub
# ... using GitHub UI ...
```

Remember that open source contributions are not just about code, but also about communication and collaboration. A well-documented and clearly described PR makes it easier for maintainers to understand, review, and merge your changes.
