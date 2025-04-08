This file is a merged representation of the entire codebase, combined into a single document by Repomix. The content has been processed where security check has been disabled.

# File Summary

## Purpose
This file contains a packed representation of the entire repository's contents.
It is designed to be easily consumable by AI systems for analysis, code review,
or other automated processes.

## File Format
The content is organized as follows:
1. This summary section
2. Repository information
3. Directory structure
4. Multiple file entries, each consisting of:
  a. A header with the file path (## File: path/to/file)
  b. The full contents of the file in a code block

## Usage Guidelines
- This file should be treated as read-only. Any changes should be made to the
  original repository files, not this packed version.
- When processing this file, use the file path to distinguish
  between different files in the repository.
- Be aware that this file may contain sensitive information. Handle it with
  the same level of security as you would the original repository.

## Notes
- Some files may have been excluded based on .gitignore rules and Repomix's configuration
- Binary files are not included in this packed representation. Please refer to the Repository Structure section for a complete list of file paths, including binary files
- Files matching patterns in .gitignore are excluded
- Files matching default ignore patterns are excluded
- Security check has been disabled - content may contain sensitive information

## Additional Info

# Directory Structure
```
.streamlit/
  config.toml
  style.css
src/
  components/
    __init__.py
    asset_tab.py
    distributional_tab.py
    financial_tab.py
    market_tab.py
    monte_carlo_tab.py
    sidebar.py
  model/
    __init__.py
    kerbside_model.py
    monte_carlo.py
  utils/
    __init__.py
    config.py
    conversion_utils.py
    parameters.py
    plot_utils.py
  __init__.py
.gitignore
app.py
LICENSE
README.md
requirements.txt
```

# Files

## File: .streamlit/config.toml
````toml
[theme]
primaryColor = "#1976D2"
backgroundColor = "#FFFFFF"
secondaryBackgroundColor = "#F0F2F6"
textColor = "#262730"
font = "sans-serif"

[server]
enableCORS = false
enableXsrfProtection = false

[browser]
gatherUsageStats = false
````

## File: .streamlit/style.css
````css
/* Improved styling for Streamlit */

.main .block-container {
    padding-top: 2rem;
    padding-bottom: 2rem;
    max-width: 1200px;
}

h1, h2, h3, h4 {
    margin-top: 1rem !important;
    margin-bottom: 1rem !important;
    font-weight: 600 !important;
}

h1 {
    color: #1976D2 !important;
    font-size: 2.2rem !important;
}

h2 {
    color: #2E3B4E !important;
    font-size: 1.8rem !important;
}

h3 {
    color: #2E3B4E !important;
    font-size: 1.4rem !important;
    margin-top: 1.5rem !important;
}

/* Basic tab styling */
.stTabs [data-baseweb="tab-list"] {
    gap: 0px;
    background-color: #F0F2F6;
    border-radius: 4px 4px 0 0;
    padding: 0.5rem 0.5rem 0 0.5rem;
}

.stTabs [data-baseweb="tab"] {
    height: 40px;
    white-space: nowrap;
    font-size: 14px;
    color: #505050;
    border-radius: 4px 4px 0 0;
    border: 1px solid transparent;
    border-bottom: none;
    padding: 10px 16px;
    background-color: #F8F8F8;
}

.stTabs [data-baseweb="tab"][aria-selected="true"] {
    color: #1976D2;
    font-weight: 600;
    background-color: white;
    border-color: #E0E0E0;
    border-bottom: 2px solid white;
}

.stTabs [data-baseweb="tab-highlight"] {
    background-color: transparent;
}

.stTabs [data-baseweb="tab-panel"] {
    padding: 1rem;
    border: 1px solid #E0E0E0;
    border-top: none;
    border-radius: 0 0 4px 4px;
    background-color: white;
}

/* Metric styling */
[data-testid="stMetricValue"] {
    font-size: 1.4rem !important;
    font-weight: 600 !important;
    color: #1976D2 !important;
}

[data-testid="stMetricLabel"] {
    font-weight: 500 !important;
}

/* Chart container styling */
[data-testid="stArrowVegaLiteChart"] {
    background-color: white;
    border-radius: 5px;
    padding: 1rem;
    box-shadow: 0 2px 5px rgba(0,0,0,0.05);
}
````

## File: src/components/__init__.py
````python
"""
UI components for the Kerbside Model Streamlit app.

This package contains reusable UI components for the Streamlit interface.
"""
````

## File: src/components/asset_tab.py
````python
"""
Asset Evolution tab component for the Kerbside Model app.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

def render_asset_tab(model_results):
    """
    Render the Asset Evolution tab.
    
    Args:
        model_results: Dictionary of model results
    """
    st.header("Asset Evolution")
    
    # Extract key results
    summary = model_results["summary"]
    rab_df = model_results["rab"]
    rollout_df = model_results["rollout"]
    
    # Display key metrics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            "Total Chargers Deployed", 
            f"{summary['total_chargers']:,.0f}",
            help="Total number of chargers deployed over the program"
        )
    
    with col2:
        st.metric(
            "Peak RAB Value", 
            f"${summary['peak_rab']/1e6:.1f}M",
            help="Maximum value of the Regulated Asset Base"
        )
    
    with col3:
        st.metric(
            "Peak RAB Year", 
            f"Year {summary['peak_rab_year']}",
            help="Year in which the RAB reaches its maximum value"
        )
    
    # Charger deployment charts
    st.subheader("Charger Deployment")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Annual deployment
        fig = px.bar(
            rollout_df,
            x=rollout_df.index,
            y="annual_chargers",
            title="Annual Charger Deployment",
            labels={"annual_chargers": "Chargers Deployed", "index": "Year"}
        )
        
        fig.update_layout(
            xaxis=dict(tickmode='linear', dtick=1),
            yaxis=dict(title="Number of Chargers"),
            hovermode="x unified"
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Cumulative deployment
        fig = px.line(
            rollout_df,
            x=rollout_df.index,
            y="cumulative_chargers",
            title="Cumulative Chargers",
            labels={"cumulative_chargers": "Cumulative Chargers", "index": "Year"},
            markers=True
        )
        
        fig.update_layout(
            xaxis=dict(tickmode='linear', dtick=1),
            yaxis=dict(title="Number of Chargers"),
            hovermode="x unified"
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    # RAB evolution chart
    st.subheader("Regulated Asset Base Evolution")
    
    # Create a combined chart with opening RAB, additions, and closing RAB
    fig = go.Figure()
    
    fig.add_trace(
        go.Scatter(
            x=rab_df.index,
            y=rab_df["opening_rab"],
            name="Opening RAB",
            mode="lines+markers",
            line=dict(width=2)
        )
    )
    
    fig.add_trace(
        go.Scatter(
            x=rab_df.index,
            y=rab_df["closing_rab"],
            name="Closing RAB",
            mode="lines+markers",
            line=dict(width=2)
        )
    )
    
    fig.add_trace(
        go.Bar(
            x=rab_df.index,
            y=rab_df["additions"],
            name="Additions",
            marker_color="lightgreen"
        )
    )
    
    fig.add_trace(
        go.Bar(
            x=rab_df.index,
            y=-rab_df["depreciation"],
            name="Depreciation",
            marker_color="salmon"
        )
    )
    
    if "obsolescence_writeoff" in rab_df.columns:
        fig.add_trace(
            go.Bar(
                x=rab_df.index,
                y=-rab_df["obsolescence_writeoff"],
                name="Obsolescence",
                marker_color="orange"
            )
        )
    
    fig.update_layout(
        title="Regulated Asset Base Evolution",
        xaxis=dict(tickmode='linear', dtick=1, title="Year"),
        yaxis=dict(title="Amount ($)"),
        barmode="relative",
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    
    st.plotly_chart(fig, use_container_width=True)
````

## File: src/components/distributional_tab.py
````python
"""
Distributional Impact tab component for the Kerbside Model app.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from src.utils.parameters import DEFAULT_MEDIAN_INCOME, INCOME_QUINTILES, ENERGY_BURDEN, EV_LIKELIHOOD

def render_distributional_tab(model_results):
    """
    Render the Distributional Impact tab.
    
    Args:
        model_results: Dictionary of model results
    """
    st.header("Distributional Impact Analysis")
    
    # Extract key results
    summary = model_results["summary"]
    avg_bill_impact = summary['avg_bill_impact']
    
    st.markdown("""
    This analysis shows how the same dollar bill impact affects households differently based on income level.
    While all households pay the same amount on their utility bills, this represents a different proportion
    of each household's income and energy spending.
    """)
    
    # Calculate actual income values from the quintile percentages
    income_quintiles_absolute = {
        quintile: DEFAULT_MEDIAN_INCOME * percentage
        for quintile, percentage in INCOME_QUINTILES.items()
    }
    
    # Calculate impacts by quintile
    quintile_impacts = []
    
    # Calculate the bill impact in dollars (same for all households)
    flat_bill_impact = avg_bill_impact
    
    for quintile, percentage in INCOME_QUINTILES.items():
        # Calculate income using the percentages from constants
        income = DEFAULT_MEDIAN_INCOME * percentage
        
        # Calculate impacts
        current_energy_cost = income * ENERGY_BURDEN[quintile]
        
        # Percentage impact on income
        pct_income_impact = (flat_bill_impact / income) * 100
        
        # EV benefit calculation
        benefit_factor = EV_LIKELIHOOD[quintile]
        
        quintile_impacts.append({
            "Quintile": quintile,
            "Annual Income": f"${income:,.0f}",
            "Energy Costs": f"${current_energy_cost:,.0f}",
            "Bill Impact": f"${flat_bill_impact:.2f}",
            "% of Income": f"{pct_income_impact:.3f}%",
            "EV Ownership Likelihood": f"{benefit_factor:.1f}x"
        })

    # Calculate regressivity metrics
    lowest_quintile_income = DEFAULT_MEDIAN_INCOME * INCOME_QUINTILES["Quintile 1 (Lowest)"]
    highest_quintile_income = DEFAULT_MEDIAN_INCOME * INCOME_QUINTILES["Quintile 5 (Highest)"]
    
    lowest_quintile_pct_impact = (avg_bill_impact / lowest_quintile_income) * 100
    highest_quintile_pct_impact = (avg_bill_impact / highest_quintile_income) * 100
    
    # Calculate actual regressivity ratio - exact same calculation as in Financial Overview tab
    regressivity_ratio = lowest_quintile_pct_impact / highest_quintile_pct_impact
    
    # Show regressivity metrics
    st.subheader("Regressivity Metrics")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            "Income Impact Ratio", 
            f"{regressivity_ratio:.2f}x",
            help="How many times greater the impact is on lowest vs. highest income quintile"
        )
    
    with col2:
        st.metric(
            "Benefit Ratio",
            f"{EV_LIKELIHOOD['Quintile 5 (Highest)'] / EV_LIKELIHOOD['Quintile 1 (Lowest)']:.1f}x",
            help="How many times more likely highest income quintile benefits from EV chargers"
        )
    
    with col3:
        st.metric(
            "NPV of Bill Impacts", 
            f"${summary['npv_bill_impact']:.2f}",
            help="Net present value of bill impacts over 15 years"
        )
        
    # Create dataframe and display table
    impact_df = pd.DataFrame(quintile_impacts)
    st.table(impact_df)

    # Visualisation of impact as % of income
    st.subheader("Bill Impact as Percentage of Income")
    
    pct_income_values = [float(qi["% of Income"].replace("%", "")) for qi in quintile_impacts]
    
    fig = px.bar(
        x=list(INCOME_QUINTILES.keys()),
        y=pct_income_values,
        labels={"x": "Income Quintile", "y": "Percentage of Annual Income (%)"},
        title="Bill Impact as Percentage of Income by Quintile"
    )
    
    fig.update_layout(yaxis_ticksuffix="%")
    st.plotly_chart(fig, use_container_width=True)
    
    # Combined chart showing benefits vs. costs
    st.subheader("Benefits vs. Costs by Income Quintile")
    
    fig = go.Figure()
    
    # Add bar for income impact
    fig.add_trace(
        go.Bar(
            x=list(INCOME_QUINTILES.keys()),
            y=pct_income_values,
            name="Cost (% of Income)",
            marker_color="firebrick"
        )
    )
    
    # Add bar for EV ownership likelihood
    fig.add_trace(
        go.Bar(
            x=list(INCOME_QUINTILES.keys()),
            y=list(EV_LIKELIHOOD.values()),
            name="Benefit (EV Ownership Likelihood)",
            marker_color="forestgreen"
        )
    )
    
    fig.update_layout(
        barmode='group',
        title="Costs vs. Benefits Distribution",
        xaxis_title="Income Quintile",
        yaxis_title="Relative Value",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Explanation of distributional impacts
    st.markdown(f"""
    ### Understanding Regressivity in Utility Programs
    
    The charts above illustrate the regressivity of the EV charger program:
    
    - **Same Dollar Amount, Different Impact**: The same dollar amount represents 
        a much larger percentage of income for lower-income households.
      
    - **Energy Burden**: Lower-income households already spend a higher percentage of their income on energy costs,
      making any additional costs more impactful.
      
    - **Benefits Accrue Unequally**: Higher-income households are more likely to own EVs and therefore
      directly benefit from the charger infrastructure, while lower-income households bear the costs with less benefit.
      
    - **Regressivity Ratio**: The bill impact is {regressivity_ratio:.2f} times more burdensome for the lowest income quintile 
      compared to the highest income quintile when measured as a percentage of income.
    """)
````

## File: src/components/financial_tab.py
````python
"""
Financial Overview tab component for the Kerbside Model app.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from src.utils.parameters import DEFAULT_MEDIAN_INCOME, INCOME_QUINTILES
from src.utils.plot_utils import create_line_chart, create_stacked_area_chart
from src.utils.conversion_utils import format_currency

def render_financial_tab(model_results):
 
    st.header("Financial Overview")
    
    # Extract key results
    summary = model_results["summary"]
    revenue_df = model_results["revenue"]
    
    # Calculate actual income values from the quintile percentages
    income_quintiles_absolute = {
        quintile: DEFAULT_MEDIAN_INCOME * percentage
        for quintile, percentage in INCOME_QUINTILES.items()
    }
    
    # Calculate percentage impact on income for lowest and highest quintiles
    avg_bill_impact = summary['avg_bill_impact']
    
    lowest_quintile_income = income_quintiles_absolute["Quintile 1 (Lowest)"]
    highest_quintile_income = income_quintiles_absolute["Quintile 5 (Highest)"]
    
    lowest_quintile_pct_impact = (avg_bill_impact / lowest_quintile_income) * 100
    highest_quintile_pct_impact = (avg_bill_impact / highest_quintile_income) * 100
    
    # Calculate regressivity ratio
    regressivity_ratio = lowest_quintile_pct_impact / highest_quintile_pct_impact
    
    # Show key metrics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            "Average Annual Bill Impact", 
            format_currency(summary['avg_bill_impact']),
            help="Average annual increase in household bills"
        )
        
        st.metric(
            "NPV of Bill Impacts", 
            format_currency(summary['npv_bill_impact']),
            help="Net present value of bill impacts over 15 years"
        )
    
    with col2:
        st.metric(
            "Peak Bill Impact", 
            format_currency(summary['peak_bill_impact']),
            help="Maximum annual bill impact"
        )
        
        st.metric(
            "Total Bill Impact", 
            format_currency(summary['total_bill_impact']),
            help="Total cumulative bill impact over 15 years"
        )
    
    with col3:
        st.metric(
            "Total Revenue Requirement", 
            format_currency(summary['total_revenue'], millions=True),
            help="Total revenue required for the program"
        )
        
        # Use the properly calculated regressivity ratio
        st.metric(
            "Regressivity Factor", 
            f"{regressivity_ratio:.2f}x",
            help="How many times greater the impact is on lowest vs. highest income quintile"
        )
    
    # Bill impact charts
    st.subheader("Bill Impact Analysis")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Annual bill impact - using utility function
        fig = create_line_chart(
            revenue_df,
            revenue_df.index,
            "bill_impact",
            "Annual Bill Impact",
            y_label="Bill Impact ($)"
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Cumulative bill impact - using utility function
        fig = create_line_chart(
            revenue_df,
            revenue_df.index,
            "cumulative_bill_impact",
            "Cumulative Bill Impact",
            y_label="Cumulative Impact ($)"
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    # Revenue breakdown
    st.subheader("Revenue Requirement Breakdown")
    
    # Create a stacked area chart using utility function
    rev_components = ["opex", "depreciation", "return_on_capital"]
    rev_labels = {"opex": "Operating Expenses", "depreciation": "Depreciation", "return_on_capital": "Return on Capital"}
    
    fig = create_stacked_area_chart(
        revenue_df,
        "index",
        rev_components,
        "Revenue Requirement Components",
        labels=rev_labels,
        y_label="Amount ($)"
    )
    
    st.plotly_chart(fig, use_container_width=True)
````

## File: src/components/market_tab.py
````python
"""
Market Effects tab component for the Kerbside Model app.
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go


def render_market_tab(model_results):
    """
    Render the Market Competition Effects tab.
    
    Args:
        model_results: Dictionary of model results
    """
    st.header("Market Competition Effects")
    
    # Extract market data
    market_df = model_results["market"]
    
    # Market development chart
    st.subheader("Market Development")
    
    # Create a stacked area chart for charger deployment
    fig = go.Figure()
    
    fig.add_trace(
        go.Scatter(
            x=market_df.index,
            y=market_df["rab_chargers"],
            name="RAB Chargers",
            stackgroup="one",
            line=dict(width=0),
            fillcolor="rgb(26, 118, 255)"
        )
    )
    
    fig.add_trace(
        go.Scatter(
            x=market_df.index,
            y=market_df["actual_private"],
            name="Private Market Chargers",
            stackgroup="one",
            line=dict(width=0),
            fillcolor="rgb(0, 200, 0)"
        )
    )
    
    # Add baseline private market line
    fig.add_trace(
        go.Scatter(
            x=market_df.index,
            y=market_df["baseline_private"],
            name="Baseline Private (No RAB)",
            mode="lines",
            line=dict(color="green", width=2, dash="dash")
        )
    )
    
    fig.update_layout(
        title="Charger Deployment by Market Segment",
        xaxis=dict(tickmode='linear', dtick=1, title="Year"),
        yaxis=dict(title="Number of Chargers"),
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Market displacement analysis
    st.subheader("Market Displacement Analysis")
    
    # Create a line chart showing displaced private market
    fig = px.area(
        market_df,
        x=market_df.index,
        y="displaced_private",
        title="Private Market Displacement",
        labels={
            "displaced_private": "Displaced Chargers",
            "index": "Year"
        }
    )
    
    fig.update_layout(
        xaxis=dict(tickmode='linear', dtick=1),
        yaxis=dict(title="Number of Chargers"),
        hovermode="x unified"
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Key metrics
    col1, col2 = st.columns(2)
    
    with col1:
        final_year = market_df.index[-1]
        
        displaced_pct = (
            (market_df.loc[final_year, "baseline_private"] - market_df.loc[final_year, "actual_private"]) / 
            market_df.loc[final_year, "baseline_private"] * 100
        )
        
        st.metric(
            "Final Private Market Displacement", 
            f"{displaced_pct:.1f}%",
            help="Percentage of private market displaced by RAB in final year"
        )
    
    with col2:
        market_growth = (
            market_df.loc[final_year, "total_with_rab"] - market_df.loc[final_year, "total_without_rab"]
        )
        
        market_growth_pct = (
            market_growth / market_df.loc[final_year, "total_without_rab"] * 100
        )
        
        st.metric(
            "Net Market Effect", 
            f"{market_growth_pct:.1f}%",
            help="Percentage change in total market size compared to baseline"
        )
````

## File: src/components/monte_carlo_tab.py
````python
"""
Monte Carlo tab component for the Kerbside Model app.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
from src.model.monte_carlo import run_monte_carlo
from src.utils.config import (
    MAX_MONTE_CARLO_SIMULATIONS,
    DEFAULT_CHART_HEIGHT,
    DEFAULT_COLOR_SCHEME,
    CURRENCY_FORMAT
)
from src.utils.conversion_utils import format_currency


def render_monte_carlo_tab(model_results, model):
    """
    Render the Monte Carlo tab.
    
    Args:
        model_results: Dictionary of model results
        model: KerbsideModel instance for simulation
    """
    st.header("Monte Carlo Simulation")
    
    st.markdown("""
    Run a Monte Carlo simulation to explore the effect of parameter uncertainty on model outcomes.
    The simulation will vary key parameters within a reasonable range to understand the sensitivity
    of results to different inputs.
    """)
    
    col1, col2 = st.columns([1, 3])
    
    with col1:
        n_simulations = st.number_input(
            "Number of Simulations",
            min_value=100,
            max_value=MAX_MONTE_CARLO_SIMULATIONS,
            value=200,
            step=100,
            help="More simulations provide better results but take longer"
        )
        
        run_mc_button = st.button("Run Simulation", use_container_width=True)
    
    # Run Monte Carlo simulation if requested
    if run_mc_button:
        with st.spinner(f"Running {n_simulations} simulations..."):
            # Use the new monte_carlo module instead of the model method
            mc_results = run_monte_carlo(model, n_simulations=n_simulations)
            st.session_state.mc_results = mc_results
    
    # Display Monte Carlo results if available
    if 'mc_results' in st.session_state:
        mc_results = st.session_state.mc_results
        results_df = mc_results["results_df"]
        summary_stats = mc_results["summary_stats"]
        
        # Display histogram of bill impacts
        st.subheader("Distribution of Bill Impacts")
        
        col1, col2 = st.columns(2)
        
        with col1:
            fig = px.histogram(
                results_df,
                x="avg_bill_impact",
                nbins=20,
                title="Average Annual Bill Impact",
                labels={"avg_bill_impact": "Average Annual Bill Impact ($)"},
                color_discrete_sequence=[px.colors.sequential.Blues[5]]
            )
            
            # Format the mean value correctly
            mean_value = summary_stats["avg_bill_impact_mean"]
            mean_label = format_currency(mean_value)
            
            fig.add_vline(
                x=mean_value, 
                line_dash="dash", 
                line_color="red",
                annotation_text=f"Mean: {mean_label}"
            )
            
            fig.update_layout(
                xaxis=dict(title="Average Annual Bill Impact ($)"),
                yaxis=dict(title="Frequency"),
                showlegend=False,
                height=DEFAULT_CHART_HEIGHT
            )
            
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            fig = px.histogram(
                results_df,
                x="peak_bill_impact",
                nbins=20,
                title="Peak Annual Bill Impact",
                labels={"peak_bill_impact": "Peak Annual Bill Impact ($)"},
                color_discrete_sequence=[px.colors.sequential.Blues[5]]
            )
            
            # Format the mean value correctly
            mean_value = summary_stats["peak_bill_impact_mean"]
            mean_label = format_currency(mean_value)
            
            fig.add_vline(
                x=mean_value, 
                line_dash="dash", 
                line_color="red",
                annotation_text=f"Mean: {mean_label}"
            )
            
            fig.update_layout(
                xaxis=dict(title="Peak Annual Bill Impact ($)"),
                yaxis=dict(title="Frequency"),
                showlegend=False,
                height=DEFAULT_CHART_HEIGHT
            )
            
            st.plotly_chart(fig, use_container_width=True)
        
        # Display summary statistics
        st.subheader("Summary Statistics")
        
        # Create a table of statistics for key metrics
        metrics = ["avg_bill_impact", "peak_bill_impact", "npv_bill_impact", "total_bill_impact"]
        metric_labels = {
            "avg_bill_impact": "Average Annual Bill Impact",
            "peak_bill_impact": "Peak Annual Bill Impact",
            "npv_bill_impact": "NPV of Bill Impacts",
            "total_bill_impact": "Total Bill Impact"
        }
        
        stats_data = []
        
        for metric in metrics:
            stats_data.append({
                "Metric": metric_labels.get(metric, metric),
                "Mean": format_currency(summary_stats[f"{metric}_mean"]),
                "Median": format_currency(summary_stats[f"{metric}_median"]),
                "Std Dev": format_currency(summary_stats[f"{metric}_std"]),
                "10th %ile": format_currency(summary_stats[f"{metric}_p10"]),
                "90th %ile": format_currency(summary_stats[f"{metric}_p90"])
            })
        
        stats_df = pd.DataFrame(stats_data)
        st.table(stats_df)
        
        # Display parameter sensitivities
        st.subheader("Parameter Sensitivities")
        
        if "correlations" in summary_stats:
            # Get correlations for average bill impact
            bill_impact_corr = summary_stats["correlations"].get("avg_bill_impact", {})
            
            if bill_impact_corr:
                # Create a horizontal bar chart
                corr_df = pd.DataFrame({
                    "Parameter": list(bill_impact_corr.keys()),
                    "Correlation": list(bill_impact_corr.values())
                })
                
                # Sort by absolute correlation
                corr_df["AbsCorr"] = corr_df["Correlation"].abs()
                corr_df = corr_df.sort_values("AbsCorr", ascending=False).head(10)
                
                fig = px.bar(
                    corr_df,
                    y="Parameter",
                    x="Correlation",
                    title="Parameter Sensitivity to Average Bill Impact",
                    orientation="h",
                    color="Correlation",
                    color_continuous_scale=px.colors.diverging.RdBu_r
                )
                
                fig.update_layout(
                    xaxis=dict(title="Correlation Coefficient"),
                    yaxis=dict(title=""),
                    coloraxis_showscale=False,
                    height=DEFAULT_CHART_HEIGHT
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                st.markdown("""
                The chart above shows the correlation between each parameter and the average bill impact.
                A positive correlation means that increasing the parameter increases the bill impact,
                while a negative correlation means that increasing the parameter decreases the bill impact.
                The absolute value indicates the strength of the relationship.
                """)
            else:
                st.info("No correlation data available.")
        else:
            st.info("No sensitivity analysis data available.")
````

## File: src/components/sidebar.py
````python
"""
Sidebar component for parameter input in the Kerbside Model app.
"""

import streamlit as st
from src.utils.parameters import (
    DEFAULT_CHARGERS_PER_YEAR,
    DEFAULT_DEPLOYMENT_YEARS,
    DEFAULT_DEPLOYMENT_DELAY,
    DEFAULT_CAPEX_PER_CHARGER,
    DEFAULT_OPEX_PER_CHARGER,
    DEFAULT_ASSET_LIFE,
    DEFAULT_WACC,
    DEFAULT_EFFICIENCY,
    DEFAULT_EFFICIENCY_DEGRADATION,
    DEFAULT_TECH_OBSOLESCENCE_RATE,
    DEFAULT_MARKET_DISPLACEMENT
)
from src.utils.conversion_utils import percentage_to_decimal

def create_sidebar_parameters():
    """
    Create the sidebar with parameter input sections.
    
    Returns:
        dict: Dictionary of model parameters
    """
    with st.sidebar:
        st.header("Model Parameters")
        
        # Create tabs for Deployment and Financial parameters
        deployment_tab, financial_tab = st.tabs(["Deployment", "Financial"])
        
        # Deployment Parameters Tab
        with deployment_tab:
            chargers_per_year = st.number_input(
                "Chargers per Year (#/year)",
                min_value=1000,
                max_value=10000,
                value=DEFAULT_CHARGERS_PER_YEAR,
                step=200,
                help="Number of chargers deployed annually"
            )
            
            deployment_years = st.slider(
                "Deployment Period (years)",
                min_value=1,
                max_value=10,
                value=DEFAULT_DEPLOYMENT_YEARS,
                step=1,
                help="Total number of years over which chargers are deployed"
            )
            
            deployment_delay = st.slider(
                "Deployment Delay Factor",
                min_value=0.5,
                max_value=2.0,
                value=DEFAULT_DEPLOYMENT_DELAY,
                step=0.1,
                help="Value >1 means slower deployment, <1 means faster deployment"
            )
            
            tech_obsolescence_rate = st.slider(
                "Technology Obsolescence Rate (%)",
                min_value=0.0,
                max_value=20.0,
                value=DEFAULT_TECH_OBSOLESCENCE_RATE * 100,
                step=1.0,
                format="%.1f%%",
                help="Annual rate at which technology becomes obsolete"
            )
            
            market_displacement = st.slider(
                "Market Displacement Rate (%)",
                min_value=0.0,
                max_value=100.0,
                value=DEFAULT_MARKET_DISPLACEMENT * 100,
                step=5.0,
                format="%.1f%%",
                help="Rate at which RAB displaces private market"
            )
        
        # Financial Parameters Tab
        with financial_tab:
            capex_per_charger = st.number_input(
                "CapEx per Charger ($)",
                min_value=1000,
                max_value=10000,
                value=DEFAULT_CAPEX_PER_CHARGER,
                step=100,
                help="One-time capital expenditure per charger"
            )
            
            opex_per_charger = st.number_input(
                "OpEx per Charger ($/year)",
                min_value=100,
                max_value=2000,
                value=DEFAULT_OPEX_PER_CHARGER,
                step=50,
                help="Annual operating expenditure per charger"
            )
            
            asset_life = st.slider(
                "Asset Life (Years)",
                min_value=3,
                max_value=15,
                value=DEFAULT_ASSET_LIFE,
                step=1,
                help="Expected lifetime of charger assets"
            )
            
            wacc = st.slider(
                "WACC (%)",
                min_value=5.50,
                max_value=6.50,
                value=DEFAULT_WACC * 100,
                step=0.10,
                format="%.2f",
                help="Weighted Average Cost of Capital"
            )
            
            efficiency = st.slider(
                "Efficiency Factor",
                min_value=0.5,
                max_value=1.5,
                value=DEFAULT_EFFICIENCY,
                step=0.05,
                help="Operational efficiency multiplier (1.0 = fully efficient, >1.0 = inefficient)"
            )
            
            efficiency_degradation = st.slider(
                "Annual Efficiency Change (%)",
                min_value=-5.0,
                max_value=10.0,
                value=DEFAULT_EFFICIENCY_DEGRADATION * 100,
                step=1.0,
                format="%.1f%%",
                help="Annual rate at which efficiency changes (positive = worsens, negative = improves)"
            )
        
        # Add a small note about automatic updates
        st.info("Model updates automatically when parameters change")
    
    # Convert percentage values to decimal for model using the utility function
    wacc_decimal = percentage_to_decimal(wacc)
    efficiency_degradation_decimal = percentage_to_decimal(efficiency_degradation)
    tech_obsolescence_decimal = percentage_to_decimal(tech_obsolescence_rate)
    market_displacement_decimal = percentage_to_decimal(market_displacement)
    
    # Set up parameter dictionary
    model_params = {
        # Deployment parameters
        "chargers_per_year": chargers_per_year,
        "deployment_years": deployment_years,
        "deployment_delay": deployment_delay,
        
        # Financial parameters
        "capex_per_charger": capex_per_charger,
        "opex_per_charger": opex_per_charger,
        "asset_life": asset_life,
        "wacc": wacc_decimal,
        
        # Efficiency parameters
        "efficiency": efficiency,
        "efficiency_degradation": efficiency_degradation_decimal,
        "tech_obsolescence_rate": tech_obsolescence_decimal,
        "market_displacement": market_displacement_decimal
    }
    
    return model_params
````

## File: src/model/__init__.py
````python
"""Kerbside EV Charger RAB model package."""

from .kerbside_model import KerbsideModel

__all__ = ["KerbsideModel"]
````

## File: src/model/kerbside_model.py
````python
"""
Kerbside Model - EV Charger RAB economic model.

This model simulates the financial impacts of deploying electric vehicle (EV) chargers 
through a Regulated Asset Base (RAB) approach.
"""

from typing import Dict, List, Any, Optional, TypedDict
import numpy as np
import pandas as pd
import streamlit as st
from src.utils.parameters import (
    DEFAULT_YEARS, 
    DEFAULT_CHARGERS_PER_YEAR, 
    DEFAULT_CAPEX_PER_CHARGER, 
    DEFAULT_OPEX_PER_CHARGER,
    DEFAULT_ASSET_LIFE, 
    DEFAULT_WACC, 
    DEFAULT_CUSTOMER_BASE, 
    DEFAULT_REVENUE_PER_CHARGER,
    DEFAULT_DEPLOYMENT_YEARS, 
    DEFAULT_DEPLOYMENT_DELAY,
    DEFAULT_EFFICIENCY,
    DEFAULT_EFFICIENCY_DEGRADATION,
    DEFAULT_TECH_OBSOLESCENCE_RATE,
    DEFAULT_MARKET_DISPLACEMENT,
    DEFAULT_INITIAL_PRIVATE_CHARGERS, 
    DEFAULT_PRIVATE_GROWTH_RATE,
    DEFAULT_SATURATION_TIME_CONSTANT,
    DEFAULT_OBSOLESCENCE_FACTOR
)

# Type definitions for model outputs
class ModelResults(TypedDict):
    rollout: pd.DataFrame      # Charger deployment data
    depreciation: pd.DataFrame # Depreciation calculations
    rab: pd.DataFrame          # Regulated Asset Base evolution
    revenue: pd.DataFrame      # Revenue requirements and bill impacts
    market: pd.DataFrame       # Market competition effects
    summary: Dict[str, float]  # Key performance metrics

# Define a standalone cached function for calculations
@st.cache_data
def run_model_calculations(
    chargers_per_year: float,
    deployment_years: int,
    deployment_delay: float,
    capex_per_charger: float,
    opex_per_charger: float,
    asset_life: int,
    wacc: float,
    customer_base: int,
    third_party_revenue: float,
    efficiency: float,
    efficiency_degradation: float,
    tech_obsolescence_rate: float,
    market_displacement: float
) -> ModelResults:
    """
    Run model calculations with caching.
    
    This standalone function allows for proper Streamlit caching by avoiding 
    class methods with 'self' parameters that cannot be hashed.
    
    Parameters:
        chargers_per_year: Annual charger deployment rate
        deployment_years: Period over which chargers are deployed
        deployment_delay: Factor to adjust deployment speed
        capex_per_charger: Capital expenditure per charger
        opex_per_charger: Annual operating expense per charger
        asset_life: Expected lifetime of charger assets
        wacc: Weighted Average Cost of Capital
        customer_base: Number of utility customers
        third_party_revenue: Revenue per charger from third parties
        efficiency: Operational efficiency factor
        efficiency_degradation: Annual change in efficiency
        tech_obsolescence_rate: Rate of technology obsolescence
        market_displacement: Rate at which RAB deployment displaces private investment
        
    Returns:
        Dictionary with model results and metrics
    """
    # Create model instance and set parameters
    model = KerbsideModel({
        "chargers_per_year": chargers_per_year,
        "deployment_years": deployment_years,
        "deployment_delay": deployment_delay,
        "capex_per_charger": capex_per_charger,
        "opex_per_charger": opex_per_charger,
        "asset_life": asset_life,
        "wacc": wacc,
        "customer_base": customer_base,
        "third_party_revenue": third_party_revenue,
        "efficiency": efficiency,
        "efficiency_degradation": efficiency_degradation,
        "tech_obsolescence_rate": tech_obsolescence_rate,
        "market_displacement": market_displacement
    })
    
    # Run model calculations but bypass the run method's cache check
    return model._run_calculations()

class KerbsideModel:
    """
    This model calculates:
    - Deployment schedule for EV chargers
    - Asset depreciation and RAB evolution
    - Revenue requirements and customer bill impacts
    - Market competition effects
    - Monte Carlo simulations for sensitivity analysis
    """
    
    def __init__(self, params: Optional[Dict[str, Any]] = None):
        """Initialise the model with parameters."""
        # Default model parameters
        self.params = {
            # Deployment parameters
            "chargers_per_year": DEFAULT_CHARGERS_PER_YEAR,
            "deployment_years": DEFAULT_DEPLOYMENT_YEARS,
            "deployment_delay": DEFAULT_DEPLOYMENT_DELAY,
            
            # Financial parameters
            "capex_per_charger": DEFAULT_CAPEX_PER_CHARGER,
            "opex_per_charger": DEFAULT_OPEX_PER_CHARGER,
            "asset_life": DEFAULT_ASSET_LIFE,
            "wacc": DEFAULT_WACC,
            
            # Customer parameters
            "customer_base": DEFAULT_CUSTOMER_BASE,
            "third_party_revenue": DEFAULT_REVENUE_PER_CHARGER,
            
            # Efficiency & market parameters
            "efficiency": DEFAULT_EFFICIENCY,
            "efficiency_degradation": DEFAULT_EFFICIENCY_DEGRADATION,
            "market_displacement": DEFAULT_MARKET_DISPLACEMENT,
            "tech_obsolescence_rate": DEFAULT_TECH_OBSOLESCENCE_RATE,
        }
        
        # Update with any provided parameters
        if params:
            self.params.update(params)
        
        # Validate parameters to prevent edge cases
        self._validate_parameters()
        
        self.results = {}

    def _validate_parameters(self):
        """Validate model parameters to prevent edge cases."""
        # Ensure no divide-by-zero errors
        if self.params["asset_life"] <= 0:
            self.params["asset_life"] = DEFAULT_ASSET_LIFE
            print(f"Warning: Asset life must be positive. Reset to default value: {DEFAULT_ASSET_LIFE}")
            
        if self.params["customer_base"] <= 0:
            self.params["customer_base"] = DEFAULT_CUSTOMER_BASE
            print(f"Warning: Customer base must be positive. Reset to default value: {DEFAULT_CUSTOMER_BASE}")
            
        # Ensure reasonable values for percentage-based parameters
        if self.params["wacc"] < 0:
            self.params["wacc"] = DEFAULT_WACC
            print(f"Warning: WACC must be non-negative. Reset to default value: {DEFAULT_WACC}")
            
        if self.params["tech_obsolescence_rate"] < 0:
            self.params["tech_obsolescence_rate"] = DEFAULT_TECH_OBSOLESCENCE_RATE
            print(f"Warning: Technology obsolescence rate must be non-negative. Reset to default value: {DEFAULT_TECH_OBSOLESCENCE_RATE}")
            
        if self.params["market_displacement"] < 0 or self.params["market_displacement"] > 1:
            self.params["market_displacement"] = DEFAULT_MARKET_DISPLACEMENT
            print(f"Warning: Market displacement must be between 0 and 1. Reset to default value: {DEFAULT_MARKET_DISPLACEMENT}")

    def run(self) -> ModelResults:
        """
        Run the complete model and return results.
        
        This method uses a cached standalone function to perform calculations
        to avoid issues with caching methods that have 'self' parameters.
        
        Returns:
            Dictionary with model results and metrics
        """
        # Call the standalone cached function with parameters as explicit arguments
        results = run_model_calculations(
            chargers_per_year=self.params["chargers_per_year"],
            deployment_years=self.params["deployment_years"],
            deployment_delay=self.params["deployment_delay"],
            capex_per_charger=self.params["capex_per_charger"],
            opex_per_charger=self.params["opex_per_charger"],
            asset_life=self.params["asset_life"],
            wacc=self.params["wacc"],
            customer_base=self.params["customer_base"],
            third_party_revenue=self.params["third_party_revenue"],
            efficiency=self.params["efficiency"],
            efficiency_degradation=self.params["efficiency_degradation"],
            tech_obsolescence_rate=self.params["tech_obsolescence_rate"],
            market_displacement=self.params["market_displacement"]
        )
        
        # Store results in the instance
        self.results = results
        return results
    
    def _run_calculations(self) -> ModelResults:
        """
        Run the core model calculations without caching.
        This method should not be called directly - use run() instead.
        """
        years = list(range(1, DEFAULT_YEARS + 1))
        
        # Run calculations in sequence
        rollout_df = self._calculate_rollout(years)
        depreciation_df = self._calculate_depreciation(rollout_df, years)
        rab_df = self._calculate_rab(rollout_df, depreciation_df, years)
        revenue_df = self._calculate_revenue(rollout_df, rab_df, years)
        market_df = self._calculate_market_effects(rollout_df, years)
        summary = self._calculate_summary(rollout_df, rab_df, revenue_df)
        
        # Return results
        return {
            "rollout": rollout_df,
            "depreciation": depreciation_df,
            "rab": rab_df,
            "revenue": revenue_df,
            "market": market_df,
            "summary": summary
        }
    
    def _calculate_rollout(self, years: List[int], params: Dict[str, Any] = None) -> pd.DataFrame:
        """Calculate charger deployment schedule and capital expenditure."""
        # Use self.params if no parameters are provided
        if params is None:
            params = self.params
            
        # Create DataFrame with years as index
        df = pd.DataFrame(index=years)
        
        # Determine deployment period (with optional delay factor)
        deployment_years = min(params["deployment_years"], len(years))
        if params.get("deployment_delay", DEFAULT_DEPLOYMENT_DELAY) > 1.0:
            deployment_years = min(len(years), int(deployment_years * params["deployment_delay"]))
        
        # Calculate chargers deployed annually (vectorised)
        total_chargers = params["chargers_per_year"] * params["deployment_years"]
        chargers_per_year = total_chargers / deployment_years
        
        # Initialize annual chargers column with zeros
        df["annual_chargers"] = 0
        
        # Set values for deployment years (vectorised)
        deployment_mask = df.index <= deployment_years
        df.loc[deployment_mask, "annual_chargers"] = chargers_per_year
        
        # Calculate cumulative chargers (vectorised)
        df["cumulative_chargers"] = df["annual_chargers"].cumsum()
        
        # Calculate capital expenditure (vectorised)
        df["unit_capex"] = params["capex_per_charger"]
        df["capex"] = df["annual_chargers"] * df["unit_capex"]
        
        return df
    
    def _calculate_depreciation(self, rollout_df: pd.DataFrame, years: List[int], params: Dict[str, Any] = None) -> pd.DataFrame:
        """
        Calculate asset depreciation, adjusting for technological obsolescence.
        
        This function calculates the depreciation schedule for assets based on their 
        installation year and expected lifetime. It accounts for technological
        obsolescence by reducing the effective asset life.
        """
        # Use self.params if no parameters are provided
        if params is None:
            params = self.params
            
        # Initialize depreciation dataframe
        depreciation_df = pd.DataFrame(index=years, columns=["total_depreciation"], data=0.0)
        
        # Get parameters
        base_asset_life = params["asset_life"]
        obsolescence_rate = params.get("tech_obsolescence_rate", DEFAULT_TECH_OBSOLESCENCE_RATE)
        
        # Get non-zero deployment years for vectorization
        active_vintage_years = rollout_df[rollout_df["annual_chargers"] > 0].index
        
        if len(active_vintage_years) == 0:
            return depreciation_df
            
        # Pre-calculate obsolescence factors and asset lives for all vintage years at once
        if obsolescence_rate > 0:
            # Calculate obsolescence factors based on when assets were deployed
            # Earlier deployments have longer life reduction due to technology advances
            obsolescence_factors = 1 - obsolescence_rate * (1 - np.exp(-np.array(active_vintage_years) / DEFAULT_SATURATION_TIME_CONSTANT))
            asset_lives = np.maximum(1, base_asset_life * obsolescence_factors)
        else:
            asset_lives = np.full(len(active_vintage_years), base_asset_life)
            
        # Create a matrix for depreciation calculation
        # Rows represent vintage years, columns represent calendar years
        depreciation_matrix = np.zeros((len(active_vintage_years), len(years)))
        
        for i, vintage_year in enumerate(active_vintage_years):
            capex = rollout_df.loc[vintage_year, "capex"]
            asset_life = asset_lives[i]
            annual_depr = capex / asset_life
            
            # Calculate applicable years for this vintage
            start_idx = years.index(vintage_year)
            end_idx = min(start_idx + int(asset_life), len(years))
            
            # Add depreciation to the matrix for these years
            depreciation_matrix[i, start_idx:end_idx] = annual_depr
            
        # Sum depreciation across all vintages for each calendar year
        depreciation_df["total_depreciation"] = np.sum(depreciation_matrix, axis=0)
        
        return depreciation_df
    
    def _calculate_rab(self, rollout_df: pd.DataFrame, depreciation_df: pd.DataFrame, years: List[int], params: Dict[str, Any] = None) -> pd.DataFrame:
        """
        Calculate Regulated Asset Base (RAB) evolution over time.
        
        The RAB is calculated by tracking the opening balance, adding new investments,
        subtracting depreciation and obsolescence writeoffs, and calculating the
        closing balance for each year. The average RAB is used for return calculations.
        """
        # Use self.params if no parameters are provided
        if params is None:
            params = self.params
            
        # Initialize RAB DataFrame 
        rab_df = pd.DataFrame(index=years)
        
        # Set initial columns (vectorised)
        rab_df["opening_rab"] = 0.0
        rab_df["additions"] = rollout_df["capex"]
        rab_df["depreciation"] = depreciation_df["total_depreciation"]
        rab_df["obsolescence_writeoff"] = 0.0
        rab_df["closing_rab"] = 0.0
        
        # Get obsolescence rate
        obsolescence_rate = params.get("tech_obsolescence_rate", DEFAULT_TECH_OBSOLESCENCE_RATE)
        
        # Calculate RAB evolution (still requires loop due to sequential nature)
        for i, year in enumerate(years):
            # Set opening RAB from previous closing RAB
            if i > 0:
                rab_df.loc[year, "opening_rab"] = rab_df.loc[years[i-1], "closing_rab"]
            
            # Calculate obsolescence writeoff (vectorised calculation)
            if obsolescence_rate > 0 and i > 0:
                opening_rab = rab_df.loc[year, "opening_rab"]
                rab_df.loc[year, "obsolescence_writeoff"] = opening_rab * obsolescence_rate * DEFAULT_OBSOLESCENCE_FACTOR
            
            # Calculate closing RAB (vectorised)
            rab_df.loc[year, "closing_rab"] = (
                rab_df.loc[year, "opening_rab"] + 
                rab_df.loc[year, "additions"] - 
                rab_df.loc[year, "depreciation"] -
                rab_df.loc[year, "obsolescence_writeoff"]
            )
        
        # Calculate average RAB (vectorised)
        rab_df["average_rab"] = (rab_df["opening_rab"] + rab_df["closing_rab"]) / 2
        
        return rab_df
    
    def _calculate_revenue(self, rollout_df: pd.DataFrame, rab_df: pd.DataFrame, years: List[int], params: Dict[str, Any] = None) -> pd.DataFrame:
        """
        Calculate revenue requirements and customer bill impacts.
        
        Revenue requirements have three components:
        1. Operating expenses - based on cumulative chargers and efficiency factor
        2. Depreciation - from RAB calculations
        3. Return on capital - WACC applied to average RAB
        
        Bill impacts are calculated by dividing net revenue by the customer base.
        """
        # Use self.params if no parameters are provided
        if params is None:
            params = self.params
            
        # Initialize revenue DataFrame
        revenue_df = pd.DataFrame(index=years)
        
        # Calculate efficiency factors (vectorised)
        base_efficiency = params.get("efficiency", DEFAULT_EFFICIENCY)
        degradation_rate = params.get("efficiency_degradation", DEFAULT_EFFICIENCY_DEGRADATION)
        years_array = np.array(years) - 1  # Convert to 0-based years
        revenue_df["efficiency_factor"] = base_efficiency * (1 + degradation_rate * years_array)
        
        # Calculate revenue components (all vectorised)
        # 1. Operating expenses
        revenue_df["opex"] = rollout_df["cumulative_chargers"] * params["opex_per_charger"] * revenue_df["efficiency_factor"]
        
        # 2. Depreciation
        revenue_df["depreciation"] = rab_df["depreciation"]
        
        # 3. Return on capital
        wacc = params["wacc"]
        revenue_df["wacc"] = wacc
        revenue_df["return_on_capital"] = rab_df["average_rab"] * wacc
        
        # Calculate total revenue (vectorised)
        revenue_df["total_revenue"] = (
            revenue_df["opex"] + 
            revenue_df["depreciation"] + 
            revenue_df["return_on_capital"]
        )
        
        # Calculate third-party revenue (vectorised)
        revenue_df["third_party_revenue"] = rollout_df["cumulative_chargers"] * params["third_party_revenue"]
        
        # Calculate bill impacts (vectorised)
        revenue_df["net_revenue"] = revenue_df["total_revenue"] - revenue_df["third_party_revenue"]
        revenue_df["bill_impact"] = revenue_df["net_revenue"] / params["customer_base"]
        revenue_df["cumulative_bill_impact"] = revenue_df["bill_impact"].cumsum()
        
        return revenue_df
    
    def _calculate_summary(self, rollout_df: pd.DataFrame, rab_df: pd.DataFrame, revenue_df: pd.DataFrame, params: Dict[str, Any] = None) -> Dict[str, float]:
        """
        Calculate key performance metrics for the model.
        
        This function computes various summary metrics including:
        - Net Present Value (NPV) calculations for revenue and bill impacts
        - Peak values and their corresponding years
        - Averages and totals for key metrics
        """
        # Use self.params if no parameters are provided
        if params is None:
            params = self.params
            
        years = rollout_df.index.tolist()
        
        # Calculate NPV metrics (vectorised)
        wacc = params["wacc"]
        discount_factors = 1 / (1 + wacc) ** np.array(years)
        npv_revenue = (revenue_df["total_revenue"] * discount_factors).sum()
        npv_bill_impact = (revenue_df["bill_impact"] * discount_factors).sum()
        
        # Identify peak values and years (vectorised operations)
        peak_rab = rab_df["closing_rab"].max()
        peak_rab_year = rab_df["closing_rab"].idxmax()
        peak_bill_impact = revenue_df["bill_impact"].max()
        peak_bill_year = revenue_df["bill_impact"].idxmax()
        
        # Return key metrics
        return {
            "total_chargers": float(rollout_df["cumulative_chargers"].iloc[-1]),
            "peak_rab": float(peak_rab),
            "peak_rab_year": int(peak_rab_year),
            "npv_revenue": float(npv_revenue),
            "npv_bill_impact": float(npv_bill_impact),
            "peak_bill_impact": float(peak_bill_impact),
            "peak_bill_year": int(peak_bill_year),
            "avg_bill_impact": float(revenue_df["bill_impact"].mean()),
            "total_bill_impact": float(revenue_df["bill_impact"].sum()),
            "total_revenue": float(revenue_df["total_revenue"].sum()),
            "total_opex": float(revenue_df["opex"].sum()),
            "final_efficiency_factor": float(revenue_df["efficiency_factor"].iloc[-1]),
        }
    
    def _calculate_market_effects(self, rollout_df: pd.DataFrame, years: List[int], params: Dict[str, Any] = None) -> pd.DataFrame:
        """
        Calculate private market effects of the regulated deployment.
        
        This function models how regulated asset deployment affects private market investment:
        1. Baseline private market is projected based on initial market and growth rate
        2. Market displacement effect is calculated based on time and displacement rate
        3. The actual private market is the baseline minus displacement
        4. Total charger deployment with and without RAB is calculated for comparison
        """
        # Use self.params if no parameters are provided
        if params is None:
            params = self.params
            
        # Initialize market DataFrame
        market_df = pd.DataFrame(index=years)
        
        # Perform all calculations with vectorised operations
        # 1. RAB deployment
        market_df["rab_chargers"] = rollout_df["cumulative_chargers"]
        
        # 2. Baseline private market (vectorised)
        years_zero_based = np.array(years) - 1
        market_df["baseline_private"] = DEFAULT_INITIAL_PRIVATE_CHARGERS * (1 + DEFAULT_PRIVATE_GROWTH_RATE) ** years_zero_based
        
        # 3. Calculate market displacement (vectorised)
        displacement_rate = params.get("market_displacement", DEFAULT_MARKET_DISPLACEMENT)
        saturation_factors = 1 - np.exp(-years_zero_based / DEFAULT_SATURATION_TIME_CONSTANT)
        
        market_df["displacement_factor"] = displacement_rate * saturation_factors
        market_df["displaced_private"] = market_df["baseline_private"] * market_df["displacement_factor"]
        market_df["actual_private"] = market_df["baseline_private"] - market_df["displaced_private"]
        
        # 4. Calculate total markets (vectorised)
        market_df["total_with_rab"] = market_df["rab_chargers"] + market_df["actual_private"]
        market_df["total_without_rab"] = market_df["baseline_private"]
        
        return market_df
````

## File: src/model/monte_carlo.py
````python
"""
Monte Carlo simulation for the Kerbside Model.

This module contains functionality for running sensitivity analysis through
Monte Carlo simulations of the Kerbside Model with varying parameters.
"""

from typing import Dict, List, Any, Optional, TypedDict
import numpy as np
import pandas as pd
import streamlit as st
from src.utils.parameters import (
    DEFAULT_WACC,
    DEFAULT_RANDOM_SEED,
    DEFAULT_PARAMETER_RANGES
)
from src.model.kerbside_model import KerbsideModel, run_model_calculations
from src.utils.config import (
    MAX_MONTE_CARLO_SIMULATIONS,
    USE_PARALLEL_COMPUTATION,
    N_PARALLEL_JOBS
)


class MonteCarloResults(TypedDict):
    """Results of Monte Carlo simulations."""
    results_df: pd.DataFrame       # Individual simulation results
    summary_stats: Dict[str, Any]  # Statistical summary of simulations


@st.cache_data
def run_monte_carlo(base_model: KerbsideModel, n_simulations: int = 500, 
                   parameter_ranges: Optional[Dict[str, Dict[str, Any]]] = None) -> MonteCarloResults:
    """
    Run Monte Carlo simulations to analyze sensitivity to parameter variations.
    
    This function is cached using Streamlit's cache_data decorator to prevent
    unnecessary recalculations when the same parameters are used multiple times.
    
    Args:
        base_model: Base model with default parameters
        n_simulations: Number of simulations to run
        parameter_ranges: Optional dictionary of parameter distributions
        
    Returns:
        Dictionary with simulation results and statistics
    """
    # Use default parameter ranges if none provided
    if parameter_ranges is None:
        parameter_ranges = DEFAULT_PARAMETER_RANGES
    
    # WACC is fixed and not varied
    if "wacc" in parameter_ranges:
        del parameter_ranges["wacc"]
    
    # Ensure n_simulations doesn't exceed the maximum
    n_simulations = min(n_simulations, MAX_MONTE_CARLO_SIMULATIONS)
    
    # Set random seed for reproducibility
    rng = np.random.default_rng(DEFAULT_RANDOM_SEED)
    
    # Get base parameters to simulate from
    base_params = base_model.params.copy()
    
    # Run simulations and collect results
    if USE_PARALLEL_COMPUTATION:
        results = run_parallel_simulations(base_params, parameter_ranges, n_simulations, rng)
    else:
        results = run_sequential_simulations(base_params, parameter_ranges, n_simulations, rng)
    
    # Calculate summary statistics
    results_df = pd.DataFrame(results)
    summary_stats = calculate_monte_carlo_summary(results_df)
    
    return {
        "results_df": results_df,
        "summary_stats": summary_stats
    }

def run_sequential_simulations(base_params: Dict[str, Any], 
                              parameter_ranges: Dict[str, Dict[str, Any]],
                              n_simulations: int,
                              rng: np.random.Generator) -> List[Dict[str, Any]]:
    """
    Run Monte Carlo simulations sequentially.
    
    Args:
        base_params: Base model parameters
        parameter_ranges: Dictionary of parameter distributions
        n_simulations: Number of simulations to run
        rng: Random number generator
        
    Returns:
        List of simulation results
    """
    results = []
    for i in range(n_simulations):
        # Generate random parameters for this simulation
        sim_params = generate_simulation_parameters(base_params, parameter_ranges, rng)
        
        # Run model with these parameters using the cached calculation function
        model_results = run_model_calculations(
            chargers_per_year=sim_params["chargers_per_year"],
            deployment_years=sim_params["deployment_years"],
            deployment_delay=sim_params.get("deployment_delay", base_params["deployment_delay"]),
            capex_per_charger=sim_params["capex_per_charger"],
            opex_per_charger=sim_params["opex_per_charger"],
            asset_life=sim_params["asset_life"],
            wacc=sim_params["wacc"],
            customer_base=sim_params.get("customer_base", base_params["customer_base"]),
            third_party_revenue=sim_params.get("third_party_revenue", base_params["third_party_revenue"]),
            efficiency=sim_params["efficiency"],
            efficiency_degradation=sim_params.get("efficiency_degradation", base_params["efficiency_degradation"]),
            tech_obsolescence_rate=sim_params["tech_obsolescence_rate"],
            market_displacement=sim_params["market_displacement"]
        )
        
        # Extract and store key results
        sim_result = {
            "simulation": i,
            "avg_bill_impact": model_results["summary"]["avg_bill_impact"],
            "peak_bill_impact": model_results["summary"]["peak_bill_impact"],
            "npv_bill_impact": model_results["summary"]["npv_bill_impact"],
            "total_bill_impact": model_results["summary"]["total_bill_impact"],
            "final_efficiency_factor": model_results["summary"]["final_efficiency_factor"],
        }
        
        # Store parameter values used
        for param_name in parameter_ranges.keys():
            if param_name in sim_params:
                sim_result[f"param_{param_name}"] = sim_params[param_name]
        
        results.append(sim_result)
    
    return results

def run_parallel_simulations(base_params: Dict[str, Any], 
                            parameter_ranges: Dict[str, Dict[str, Any]],
                            n_simulations: int,
                            rng: np.random.Generator) -> List[Dict[str, Any]]:
    """
    Run Monte Carlo simulations in parallel.
    
    This is a placeholder for parallel implementation. Currently falls back to sequential.
    For actual implementation, libraries like joblib or concurrent.futures could be used.
    
    Args:
        base_params: Base model parameters
        parameter_ranges: Dictionary of parameter distributions
        n_simulations: Number of simulations to run
        rng: Random number generator
        
    Returns:
        List of simulation results
    """
    # For now, we'll fall back to sequential processing
    # In a future implementation, this would use joblib or concurrent.futures
    st.warning("Parallel computation is enabled in config but not yet implemented. Using sequential processing.")
    return run_sequential_simulations(base_params, parameter_ranges, n_simulations, rng)

def generate_simulation_parameters(base_params: Dict[str, Any],
                                  parameter_ranges: Dict[str, Dict[str, Any]],
                                  rng: np.random.Generator) -> Dict[str, Any]:
    """
    Generate random parameters for a Monte Carlo simulation.
    
    Args:
        base_params: Base model parameters dictionary
        parameter_ranges: Dictionary defining parameter distribution shapes and ranges
        rng: NumPy random number generator instance
        
    Returns:
        Dictionary of parameters for a single simulation run
    """
    sim_params = base_params.copy()
    
    for param_name, param_range in parameter_ranges.items():
        if param_name not in sim_params:
            continue
        
        dist_type = param_range.get("distribution", "uniform")
        
        if dist_type == "uniform":
            min_val = param_range.get("min", sim_params[param_name] * 0.8)
            max_val = param_range.get("max", sim_params[param_name] * 1.2)
            sim_params[param_name] = rng.uniform(min_val, max_val)
            
        elif dist_type == "triangular":
            min_val = param_range.get("min", sim_params[param_name] * 0.8)
            max_val = param_range.get("max", sim_params[param_name] * 1.2)
            mode = param_range.get("mode", sim_params[param_name])
            sim_params[param_name] = rng.triangular(min_val, mode, max_val)
        
        elif dist_type == "normal":
            mean = param_range.get("mean", sim_params[param_name])
            std = param_range.get("std", sim_params[param_name] * 0.1)
            sim_params[param_name] = rng.normal(mean, std)
    
    # WACC is always fixed
    sim_params["wacc"] = DEFAULT_WACC
    
    return sim_params

@st.cache_data
def calculate_monte_carlo_summary(results_df: pd.DataFrame) -> Dict[str, Any]:
    """
    Calculate summary statistics from Monte Carlo results.
    
    This function is cached using Streamlit's cache_data decorator to prevent
    unnecessary recalculations when the same results dataframe is processed multiple times.
    
    Args:
        results_df: DataFrame containing all Monte Carlo simulation results
        
    Returns:
        Dictionary of statistical summaries for each metric
    """
    # Identify metrics columns
    metrics = [col for col in results_df.columns 
              if not col.startswith("param_") and col != "simulation"]
    
    summary = {}
    
    # Calculate statistics for each metric
    for metric in metrics:
        values = results_df[metric].values
        
        summary[f"{metric}_mean"] = float(np.mean(values))
        summary[f"{metric}_median"] = float(np.median(values))
        summary[f"{metric}_std"] = float(np.std(values))
        summary[f"{metric}_min"] = float(np.min(values))
        summary[f"{metric}_max"] = float(np.max(values))
        summary[f"{metric}_p10"] = float(np.percentile(values, 10))
        summary[f"{metric}_p90"] = float(np.percentile(values, 90))
    
    # Calculate correlations between parameters and metrics
    param_cols = [col for col in results_df.columns if col.startswith("param_")]
    correlations = {}
    
    for metric in metrics:
        metric_corrs = {}
        
        for param in param_cols:
            param_name = param.replace("param_", "")
            corr = np.corrcoef(results_df[param], results_df[metric])[0, 1]
            metric_corrs[param_name] = float(corr)
        
        # Sort by correlation magnitude
        correlations[metric] = dict(sorted(
            metric_corrs.items(),
            key=lambda x: abs(x[1]),
            reverse=True
        ))
    
    summary["correlations"] = correlations
    
    return summary
````

## File: src/utils/__init__.py
````python
"""
Utilities for the Kerbside Model Streamlit app.

This package contains utility functions and constants for the application.
"""

from src.utils.conversion_utils import (
    percentage_to_decimal,
    format_currency,
    format_percentage
)

from src.utils.plot_utils import (
    create_line_chart,
    create_stacked_area_chart,
    create_bar_chart
)
````

## File: src/utils/config.py
````python
"""
Configuration file for the Kerbside EV Charger Economic Model.

This module contains environment-specific configuration settings that can be
modified without changing the application code.
"""

# =============================================
# Application Configuration
# =============================================

# Data file paths (can be absolute or relative to application root)
DATA_PATH = "data"

# Default file paths for data imports/exports
DEFAULT_EXPORT_PATH = "exports"

# Environment-specific settings
DEBUG_MODE = False
SHOW_DETAILED_ERRORS = True

# =============================================
# User Interface Configuration
# =============================================

# Charts and visualization settings
DEFAULT_CHART_HEIGHT = 400
DEFAULT_CHART_WIDTH = 800
DEFAULT_COLOR_SCHEME = "Blues"
CHART_DECIMALS = 2

# Theme-related settings
PRIMARY_COLOR = "#1E88E5"
SECONDARY_COLOR = "#ff9e00"
BACKGROUND_COLOR = "#f0f2f6"

# =============================================
# Model Configuration
# =============================================

# Computation settings
MAX_MONTE_CARLO_SIMULATIONS = 1000
USE_PARALLEL_COMPUTATION = False  # Set to True to enable parallel computation for Monte Carlo
N_PARALLEL_JOBS = 4  # Number of parallel jobs for Monte Carlo simulation

# =============================================
# Data Export Configuration
# =============================================

# Export settings
DEFAULT_EXPORT_FORMAT = "csv"
AVAILABLE_EXPORT_FORMATS = ["csv", "excel", "json"]

# Number formatting for exports
DECIMAL_PLACES = 2
CURRENCY_FORMAT = "${:.2f}"
PERCENTAGE_FORMAT = "{:.2f}%"
````

## File: src/utils/conversion_utils.py
````python
"""
Utility functions for parameter conversions and transformations.
"""

def percentage_to_decimal(percentage_value):
    """
    Convert a percentage value to its decimal equivalent.
    
    Args:
        percentage_value (float): The percentage value (e.g., 5.95 for 5.95%)
        
    Returns:
        float: The decimal equivalent (e.g., 0.0595)
    """
    return percentage_value / 100.0

def format_currency(value, millions=False):
    """
    Format a numeric value as currency.
    
    Args:
        value (float): The value to format
        millions (bool): Whether to display in millions
        
    Returns:
        str: Formatted currency string
    """
    if millions:
        return f"${value/1e6:.1f}M"
    else:
        return f"${value:.2f}"

def format_percentage(value):
    """
    Format a decimal value as percentage.
    
    Args:
        value (float): The decimal value (e.g., 0.0595)
        
    Returns:
        str: Formatted percentage string (e.g., "5.95%")
    """
    return f"{value * 100:.2f}%"
````

## File: src/utils/parameters.py
````python
"""
Parameters for the Kerbside Model app.
"""

# =============================================
# App Configuration
# =============================================

# Page configuration
PAGE_TITLE = "Kerbside EV Charger Model"
PAGE_ICON = "🔌"
PAGE_LAYOUT = "wide"

# Tab names
TABS = [
    "Financial Overview", 
    "Asset Evolution",
    "Distributional Impact",
    "Market Effects",
    "Monte Carlo Analysis"
]

# =============================================
# Core Model Parameters
# =============================================

# Time period
DEFAULT_YEARS = 15  # Standard 15-year analysis period

# Deployment parameters
DEFAULT_CHARGERS_PER_YEAR = 6000  # Default annual charger deployment
DEFAULT_DEPLOYMENT_YEARS = 5  # Default deployment period
DEFAULT_DEPLOYMENT_DELAY = 1.0  # Default deployment delay factor (>1 means slower)

# Financial parameters
DEFAULT_CAPEX_PER_CHARGER = 6000  # Default capital cost per charger
DEFAULT_OPEX_PER_CHARGER = 500   # Default operating cost per charger
DEFAULT_ASSET_LIFE = 8    # Default asset lifetime in years
DEFAULT_WACC = 0.0595     # Default Weighted Average Cost of Capital (5.95%)

# Third-party revenue parameters
DEFAULT_REVENUE_PER_CHARGER = 100  # Default third-party revenue per charger (NOTE: Used in KerbsideModel but not in UI inputs)

# Customer parameters
DEFAULT_CUSTOMER_BASE = 1800000  # Default utility customer base

# Efficiency parameters
DEFAULT_EFFICIENCY = 1.0  # Default efficiency factor (1.0 = fully efficient)
DEFAULT_EFFICIENCY_DEGRADATION = 0.0  # Default annual efficiency degradation
DEFAULT_TECH_OBSOLESCENCE_RATE = 0.0  # Default technology obsolescence rate

# Private market parameters
DEFAULT_INITIAL_PRIVATE_CHARGERS = 1000  # Initial private market chargers
DEFAULT_PRIVATE_GROWTH_RATE = 0.2  # Annual growth rate of private market
DEFAULT_MARKET_DISPLACEMENT = 0.0  # Default market displacement rate
DEFAULT_SATURATION_TIME_CONSTANT = 5.0  # Time constant for market saturation effect

# RAB obsolescence calculation
DEFAULT_OBSOLESCENCE_FACTOR = 0.1  # Factor for obsolescence writeoff calculation

# Income data parameters
DEFAULT_MEDIAN_INCOME = 92856  # Median household income

# Income quintiles as a fraction of median income
INCOME_QUINTILES = {
    "Quintile 1 (Lowest)": 0.27, 
    "Quintile 2": 0.6,
    "Quintile 3 (Median)": 1.0,
    "Quintile 4": 1.54,
    "Quintile 5 (Highest)": 3.1
}

# Energy burden by income quintile (% of income spent on energy)
ENERGY_BURDEN = {
    "Quintile 1 (Lowest)": 0.085,  # 8.5% of income
    "Quintile 2": 0.065,
    "Quintile 3 (Median)": 0.045,
    "Quintile 4": 0.025,
    "Quintile 5 (Highest)": 0.015
}

# EV ownership likelihood multiplier
EV_LIKELIHOOD = {
    "Quintile 1 (Lowest)": 0.01,
    "Quintile 2": 0.4,
    "Quintile 3 (Median)": 0.8,
    "Quintile 4": 1.2,
    "Quintile 5 (Highest)": 1.6
}

# =============================================
# Monte Carlo Simulation Parameters
# =============================================

# Default random seed for reproducibility
DEFAULT_RANDOM_SEED = 42

# Default parameter ranges for Monte Carlo simulation
DEFAULT_PARAMETER_RANGES = {
    "capex_per_charger": {
        "distribution": "triangular",
        "min": 4500,
        "mode": 6000,
        "max": 8000
    },
    "opex_per_charger": {
        "distribution": "triangular",
        "min": 350,
        "mode": 500,
        "max": 700
    },
    "asset_life": {
        "distribution": "triangular", 
        "min": 6,
        "mode": 8,
        "max": 10
    },
    "efficiency": {
        "distribution": "triangular",
        "min": 0.9,
        "mode": 1.0,
        "max": 1.3
    },
    "tech_obsolescence_rate": {
        "distribution": "triangular",
        "min": 0.0,
        "mode": 0.05,
        "max": 0.1
    },
    "market_displacement": {
        "distribution": "triangular",
        "min": 0.0,
        "mode": 0.3,
        "max": 0.7
    }
}
````

## File: src/utils/plot_utils.py
````python
"""
Utility functions for creating consistent plots across the application.
"""

import plotly.express as px
import plotly.graph_objects as go

def create_line_chart(df, x_col, y_col, title, y_label=None, markers=True):
    """
    Create a line chart with consistent styling.
    
    Args:
        df (pd.DataFrame): Data source
        x_col: Column or index for x-axis
        y_col (str or list): Column(s) for y-axis
        title (str): Chart title
        y_label (str, optional): Custom y-axis label
        markers (bool): Whether to show markers
        
    Returns:
        plotly.graph_objects.Figure: The configured figure
    """
    if y_label is None:
        y_label = y_col if isinstance(y_col, str) else "Value"
    
    fig = px.line(
        df,
        x=x_col,
        y=y_col,
        title=title,
        labels={y_col: y_label, "index": "Year"},
        markers=markers
    )
    
    fig.update_layout(
        xaxis=dict(tickmode='linear', dtick=1),
        yaxis=dict(title=y_label),
        hovermode="x unified"
    )
    
    return fig

def create_stacked_area_chart(df, x_col, y_cols, title, labels=None, y_label="Value"):
    """
    Create a stacked area chart with consistent styling.
    
    Args:
        df (pd.DataFrame): Data source
        x_col: Column or index for x-axis
        y_cols (list): List of columns for y-axis
        title (str): Chart title
        labels (dict, optional): Dictionary mapping column names to display names
        y_label (str): Y-axis label
        
    Returns:
        plotly.graph_objects.Figure: The configured figure
    """
    if labels is None:
        labels = {}
    
    fig = go.Figure()
    
    for component in y_cols:
        fig.add_trace(
            go.Scatter(
                x=df[x_col] if x_col in df.columns else df.index,
                y=df[component],
                name=labels.get(component, component),
                stackgroup="one"
            )
        )
    
    fig.update_layout(
        title=title,
        xaxis=dict(tickmode='linear', dtick=1, title="Year"),
        yaxis=dict(title=y_label),
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    
    return fig

def create_bar_chart(df, x_col, y_col, title, color=None, y_label=None):
    """
    Create a bar chart with consistent styling.
    
    Args:
        df (pd.DataFrame): Data source
        x_col: Column for x-axis
        y_col: Column for y-axis
        title (str): Chart title
        color (str, optional): Column to use for bar colors
        y_label (str, optional): Custom y-axis label
        
    Returns:
        plotly.graph_objects.Figure: The configured figure
    """
    if y_label is None:
        y_label = y_col
    
    fig = px.bar(
        df,
        x=x_col,
        y=y_col,
        color=color,
        title=title,
        labels={y_col: y_label, x_col: x_col}
    )
    
    fig.update_layout(
        yaxis=dict(title=y_label),
        hovermode="closest"
    )
    
    return fig
````

## File: src/__init__.py
````python
"""Kerbside Model - EV Charger Economic Analysis Package."""

from src.model.kerbside_model import KerbsideModel

__all__ = ["KerbsideModel"]
````

## File: .gitignore
````
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
*.egg-info/
.installed.cfg
*.egg

# Virtual Environment
venv/
ENV/
env/

# Jupyter Notebook
.ipynb_checkpoints

# Streamlit
.streamlit/secrets.toml

# macOS
.DS_Store

# IDE
.idea/
.vscode/
*.swp
*.swo
pyrightconfig.json
.env

# Logs
*.log
````

## File: app.py
````python
"""
Streamlit app for the Kerbside EV Charger Model.

This app provides an interactive interface for the simplified EV charger model.
"""

import streamlit as st

from src.model.kerbside_model import KerbsideModel
from src.utils.parameters import (
    PAGE_TITLE, PAGE_ICON, PAGE_LAYOUT, TABS
)
from src.components.sidebar import create_sidebar_parameters
from src.components.financial_tab import render_financial_tab
from src.components.asset_tab import render_asset_tab
from src.components.distributional_tab import render_distributional_tab
from src.components.market_tab import render_market_tab
from src.components.monte_carlo_tab import render_monte_carlo_tab

# Set page configuration
st.set_page_config(
    page_title=PAGE_TITLE,
    page_icon=PAGE_ICON,
    layout=PAGE_LAYOUT
)

# App title and description
st.title("Kerbside EV Charger Economic Model")
st.markdown("""
This app analyses the economic implications of deploying electric vehicle (EV) chargers 
through a Regulated Asset Base (RAB) approach. Adjust the parameters to see how they
affect the economic outcomes.
""")

# Create sidebar for parameters
model_params = create_sidebar_parameters()

# Initialize and run the model
with st.spinner("Running model calculations..."):
    model = KerbsideModel(model_params)
    model_results = model.run()
    st.session_state.model_results = model_results
    st.session_state.model = model

# Create tabs the standard way
tab1, tab2, tab3, tab4, tab5 = st.tabs(TABS)

# Render content in each tab
with tab1:
    render_financial_tab(model_results)
    
with tab2:
    render_asset_tab(model_results)
    
with tab3:
    render_distributional_tab(model_results)
    
with tab4:
    render_market_tab(model_results)
    
with tab5:
    render_monte_carlo_tab(model_results, model)

# Footer with additional information
st.markdown("---")
st.markdown("""
**About this model**: This models the implementation of the EV charger RAB economic model.
It calculates the impact of deploying EV chargers on household energy bills, as well as the impact on private investment 
and market competition.
""")
````

## File: LICENSE
````
MIT License

Copyright (c) 2023 Edward Miller

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
````

## File: README.md
````markdown
# Kerbside EV Charger Economic Model

A streamlined economic model for analyzing the deployment of electric vehicle chargers through a Regulated Asset Base (RAB) approach.

## Overview

The Kerbside Model is a simplified implementation of an EV charger economic model that analyzes:

- Financial impacts on customer bills
- Asset base evolution over time
- Market competition effects
- Parameter sensitivity through Monte Carlo simulations

This model consolidates multiple parameters and calculations into a single, unified approach that is more maintainable and easier to understand while maintaining the accuracy of the underlying economic analysis.

## Key Features

- **Simplified parameter structure**: Reduced parameter count focused on the most impactful ones
- **Integrated calculations**: Consolidated calculation methods with vectorized operations
- **Powerful visualizations**: Interactive charts showing key metrics and trends
- **Monte Carlo simulation**: Parameter sensitivity analysis to understand uncertainty
- **Market competition effects**: Analysis of private market displacement and innovation gaps

## Installation

1. Clone this repository:
   ```
   git clone https://github.com/emil7051/kerbside_charger_model.git
   cd kerbside_charger_model
   ```

2. Create a virtual environment (optional but recommended):
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

## Usage

Run the Streamlit app:

```
streamlit run app.py
```

This will launch a web browser with the interactive model interface. Use the sidebar parameters to adjust model inputs and see the results update in real-time.

## Model Structure

The model is organized in a modular, maintainable structure:

- `src/model/kerbside_model.py`: The main model class encapsulating all calculations
- `src/components/`: UI components for the Streamlit app
  - `sidebar.py`: Parameter input sidebar
  - `financial_tab.py`: Financial overview tab
  - `asset_tab.py`: Asset evolution tab
  - `market_tab.py`: Market effects tab
  - `distributional_tab.py`: Distributional impact tab
  - `monte_carlo_tab.py`: Monte Carlo simulation tab
- `src/utils/`: Utility functions and constants
  - `constants.py`: Application-wide constants
- `app.py`: Main Streamlit app entry point

This modular structure improves code maintainability, readability, and makes it easier to extend or modify individual components.

## Parameter Descriptions

- **Deployment Parameters**:
  - `chargers_per_year`: Number of chargers deployed annually
  - `deployment_years`: Number of years for the deployment phase
  - `deployment_delay`: Factor affecting deployment time (>1 means slower)

- **Financial Parameters**:
  - `capex_per_charger`: Capital cost per charger ($)
  - `opex_per_charger`: Annual operating cost per charger ($)
  - `asset_life`: Expected lifetime of charger assets (years)
  - `wacc`: Weighted Average Cost of Capital (%)
  - `cost_decline_rate`: Annual technology cost reduction (%)

- **Efficiency Parameters**:
  - `efficiency`: Operational efficiency factor (1.0 = fully efficient)
  - `efficiency_degradation`: Annual worsening of efficiency
  - `tech_obsolescence_rate`: Rate at which technology becomes obsolete

- **Market Parameters**:
  - `market_displacement`: Rate at which RAB displaces private market

## License

This project is licensed under the MIT License - see the LICENSE file for details.
````

## File: requirements.txt
````
numpy>=1.20.0
pandas>=1.3.0
matplotlib>=3.4.0
plotly>=5.5.0
streamlit>=1.10.0
scipy>=1.7.0
````
