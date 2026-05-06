"""Basic usage example for the taguchi library."""

import numpy as np
from taguchi import TaguchiDesign


def objective_function(factors):
    """Example objective function for CNN hyperparameter tuning.

    Parameters
    ----------
    factors : list
        List of factor values. For repetitions > 1, last element is the
        repetition index.

    Returns
    -------
    dict
        Dictionary mapping response names to values.
    """
    learning_rate, batch_size, num_filters, dropout = factors[:4]

    # Simulate a noisy evaluation result
    # (In practice, this would be the result of training a CNN)
    noise = np.random.normal(0, 0.01)
    accuracy = (0.5 + 0.2 * learning_rate + 0.1 * (batch_size / 32)
                + 0.15 * num_filters - 0.1 * dropout + noise)

    return {
        "accuracy": accuracy,
        "loss": 1.0 - accuracy,
    }


def main():
    """Run a complete Taguchi design example."""
    print("Taguchi Design of Experiments Example")
    print("=" * 50)

    # Define experimental factors
    experimental_design = {
        "Learning rate": [1e-4, 1e-3],
        "Batch size": [16, 64],
        "Num filters": [16, 64],
        "Dropout rate": [0.2, 0.5],
    }

    # Create design on L16 array
    # Assign factors to columns 0, 2, 4, 6 (avoiding interactions)
    design = TaguchiDesign(
        experimental_design,
        assignation=[0, 2, 4, 6],
        matrix="L16",
    )

    print(f"\nDesign: {design.matrix_name}")
    print(f"Factors: {list(experimental_design.keys())}")
    print(f"Number of runs: {len(design.experimental_matrix)}")

    # Run the experiments
    print("\nRunning experiments...")
    design.run(
        objective_function,
        responses=["accuracy", "loss"],
        repetitions=2,  # 2 repetitions per run
    )
    print("Experiments completed.")

    # Analyze results
    print("\nAnalyzing results...")
    design.analyze()
    print("Analysis completed.")

    # Display results for accuracy
    print("\nAccuracy Analysis Results:")
    print("-" * 50)
    accuracy_df = design.taguchi_design["accuracy"]
    analysis_rows = accuracy_df.iloc[len(design.experimental_matrix):]
    print(analysis_rows)

    # Create visualizations
    print("\nGenerating visualizations...")
    design.pareto_plot(path="./pareto_plots")
    design.effect_plots(path="./effect_plots")
    print("Plots saved to pareto_plots/ and effect_plots/")

    # Save the design
    print("\nSaving design...")
    design.save("example_design.zip")
    print("Design saved to example_design.zip")

    # Load and verify
    print("\nLoading design from archive...")
    loaded_design = TaguchiDesign.load("example_design.zip")
    print(f"Loaded design: {loaded_design.matrix_name}")
    print(f"Responses: {loaded_design.responses}")
    print(f"Repetitions: {loaded_design.repetitions}")

    print("\nExample completed successfully!")


if __name__ == "__main__":
    main()
