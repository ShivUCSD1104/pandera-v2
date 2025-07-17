"""
Main module for generating Greeks Landscape 3D visualizations.

This module handles the main entry point for creating Plotly-based 3D surface
plots of options Greeks data with comprehensive error handling and validation.
"""

import plotly.graph_objects as go
import plotly.express as px
from typing import Dict, Any, Optional
import logging

from .data import GreeksDataFetcher
from .greeks_calculator import GreeksCalculator
from .validators import validator
from .exceptions import (
    GreeksLandscapeError, ValidationError, DataNotAvailableError, 
    CalculationError, DatabaseError
)
from .performance_monitor import performance_monitor, monitor_performance

logger = logging.getLogger(__name__)


@monitor_performance('full_landscape_generation')
def generate_greeks_landscape_html(
    ticker: str,
    greeks_view: str = 'All',
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
) -> Dict[str, Any]:
    """
    Generate 3D Greeks landscape visualization with comprehensive error handling.
    
    Args:
        ticker: Stock ticker symbol
        greeks_view: Which Greeks to display ('Delta', 'Gamma', 'Theta', 'Vega', 'All')
        start_date: Start date for options data (optional)
        end_date: End date for options data (optional)
        
    Returns:
        Dict containing Plotly figure JSON or error information with user-friendly messages
    """
    try:
        logger.info(f"Starting Greeks landscape generation for {ticker}, view: {greeks_view}")
        
        # Step 1: Validate all input parameters
        try:
            validated_params = validator.validate_all_parameters(
                ticker=ticker,
                greeks_view=greeks_view,
                start_date=start_date,
                end_date=end_date
            )
            logger.info(f"Input validation successful for {ticker}")
        except ValidationError as e:
            logger.warning(f"Input validation failed: {e.user_message}")
            return {
                "error": e.user_message,
                "type": e.error_type,
                "field": getattr(e, 'field', None)
            }
        
        # Use validated parameters
        ticker = validated_params['ticker']
        greeks_view = validated_params['greeks_view']
        start_date_obj = validated_params['start_date']
        end_date_obj = validated_params['end_date']
        
        # Convert date objects back to strings for data fetcher
        start_date_str = start_date_obj.strftime('%Y-%m-%d') if start_date_obj else None
        end_date_str = end_date_obj.strftime('%Y-%m-%d') if end_date_obj else None
        
        # Step 2: Initialize data fetcher and calculator
        try:
            data_fetcher = GreeksDataFetcher()
            calculator = GreeksCalculator()
            logger.debug("Initialized data fetcher and calculator")
        except Exception as e:
            logger.error(f"Failed to initialize components: {str(e)}")
            raise CalculationError(
                f"System initialization failed: {str(e)}",
                user_message="System error occurred. Please try again later."
            )
        
        # Step 3: Fetch options chain data with error handling
        try:
            options_chain = data_fetcher.fetch_options_chain(ticker, start_date_str, end_date_str)
            logger.info(f"Fetched options chain for {ticker}")
        except DatabaseError as e:
            logger.error(f"Database error fetching options for {ticker}: {str(e)}")
            return {
                "error": e.user_message,
                "type": e.error_type
            }
        except DataNotAvailableError as e:
            logger.warning(f"No data available for {ticker}: {str(e)}")
            return {
                "error": e.user_message,
                "type": e.error_type
            }
        except Exception as e:
            logger.error(f"Unexpected error fetching options data: {str(e)}")
            return {
                "error": f"Unable to fetch options data for {ticker}. Please verify the ticker symbol and try again.",
                "type": "data_error"
            }
        
        # Step 4: Validate options data availability
        if not options_chain or not options_chain.options:
            logger.warning(f"No options data found for {ticker}")
            return {
                "error": f"No options data available for {ticker}. This ticker may not have listed options or data may be temporarily unavailable.",
                "type": "data_error"
            }
        
        logger.info(f"Found {len(options_chain.options)} options for {ticker}")
        
        # Step 5: Prepare data for Greeks calculations
        try:
            greeks_data_list = data_fetcher.prepare_greeks_data(options_chain)
            logger.info(f"Prepared {len(greeks_data_list)} options for Greeks calculation")
        except Exception as e:
            logger.error(f"Error preparing Greeks data: {str(e)}")
            return {
                "error": "Unable to process options data for Greeks calculation. Please try again.",
                "type": "data_error"
            }
        
        if not greeks_data_list:
            logger.warning(f"No valid options data for Greeks calculation for {ticker}")
            return {
                "error": f"No valid options found for {ticker}. Options may be expired or have invalid data.",
                "type": "data_error"
            }
        
        # Step 6: Calculate Greeks with error handling
        try:
            calculated_greeks = calculator.calculate_batch_greeks(greeks_data_list)
            valid_greeks = [g for g in calculated_greeks if g.delta is not None]
            logger.info(f"Successfully calculated Greeks for {len(valid_greeks)} options")
        except CalculationError as e:
            logger.error(f"Greeks calculation error: {str(e)}")
            return {
                "error": e.user_message,
                "type": e.error_type
            }
        except Exception as e:
            logger.error(f"Unexpected error in Greeks calculation: {str(e)}")
            return {
                "error": "Greeks calculation failed. Please check your parameters and try again.",
                "type": "calculation_error"
            }
        
        if not valid_greeks:
            logger.warning(f"No valid Greeks calculated for {ticker}")
            return {
                "error": f"Unable to calculate Greeks for {ticker}. Options data may be insufficient or invalid.",
                "type": "calculation_error"
            }
        
        # Step 7: Create surface data for visualization
        try:
            strikes_grid, expiries_grid, greeks_surfaces = data_fetcher.create_greeks_surface_data(valid_greeks)
            logger.info(f"Created surface data with {strikes_grid.size} data points")
        except Exception as e:
            logger.error(f"Error creating surface data: {str(e)}")
            return {
                "error": "Unable to create visualization data. Please try again.",
                "type": "generation_error"
            }
        
        if strikes_grid.size == 0 or expiries_grid.size == 0:
            logger.warning(f"Insufficient surface data for {ticker}")
            return {
                "error": f"Insufficient data to create Greeks visualization for {ticker}. Need more options with different strikes and expiries.",
                "type": "data_error"
            }
        
        # Step 8: Create the 3D visualization
        try:
            fig = _create_greeks_3d_plot(
                strikes_grid, 
                expiries_grid, 
                greeks_surfaces, 
                ticker, 
                greeks_view,
                options_chain.underlying_price
            )
            logger.info(f"Successfully created 3D plot for {ticker}")
        except Exception as e:
            logger.error(f"Error creating 3D plot: {str(e)}")
            return {
                "error": "Unable to create 3D visualization. Please try again.",
                "type": "generation_error"
            }
        
        # Step 9: Convert to JSON with error handling
        try:
            fig_json = fig.to_json()
            logger.info(f"Successfully generated Greeks landscape for {ticker}")
            return fig_json
        except Exception as e:
            logger.error(f"Error converting plot to JSON: {str(e)}")
            return {
                "error": "Unable to generate final visualization. Please try again.",
                "type": "generation_error"
            }
        
    except ValidationError as e:
        # Re-raise validation errors to be handled by outer try-catch
        logger.warning(f"Validation error: {e.user_message}")
        return {
            "error": e.user_message,
            "type": e.error_type,
            "field": getattr(e, 'field', None)
        }
    except GreeksLandscapeError as e:
        # Handle all custom Greeks Landscape errors
        logger.error(f"Greeks Landscape error: {str(e)}")
        return {
            "error": e.user_message,
            "type": e.error_type
        }
    except Exception as e:
        # Handle any unexpected errors
        logger.error(f"Unexpected error generating Greeks landscape: {str(e)}", exc_info=True)
        return {
            "error": "An unexpected error occurred while generating the Greeks landscape. Please try again later.",
            "type": "system_error"
        }


def _create_greeks_3d_plot(
    strikes_grid: Any,
    expiries_grid: Any,
    greeks_surfaces: Dict[str, Any],
    ticker: str,
    greeks_view: str,
    underlying_price: float
) -> go.Figure:
    """
    Create 3D surface plots for Greeks visualization with toggle functionality.
    
    Args:
        strikes_grid: Meshgrid of strike prices
        expiries_grid: Meshgrid of time to expiry values
        greeks_surfaces: Dictionary containing Greeks surface data
        ticker: Stock ticker symbol
        greeks_view: Which Greeks to display
        underlying_price: Current underlying asset price
        
    Returns:
        Plotly Figure object with 3D Greeks surfaces
    """
    fig = go.Figure()
    
    # Define colors and properties for each Greek
    greeks_config = {
        'delta': {
            'color': 'Viridis',
            'name': 'Delta',
            'description': 'Price Sensitivity',
            'visible': True if greeks_view in ['Delta', 'All'] else False
        },
        'gamma': {
            'color': 'Plasma',
            'name': 'Gamma', 
            'description': 'Delta Sensitivity',
            'visible': True if greeks_view in ['Gamma', 'All'] else False
        },
        'theta': {
            'color': 'Inferno',
            'name': 'Theta',
            'description': 'Time Decay',
            'visible': True if greeks_view in ['Theta', 'All'] else False
        },
        'vega': {
            'color': 'Cividis',
            'name': 'Vega',
            'description': 'Volatility Sensitivity', 
            'visible': True if greeks_view in ['Vega', 'All'] else False
        }
    }
    
    # Add surface for each Greek
    for greek_name, config in greeks_config.items():
        if greek_name in greeks_surfaces:
            # Create hover text with detailed information
            hover_text = _create_hover_text(
                strikes_grid, 
                expiries_grid, 
                greeks_surfaces[greek_name],
                greek_name,
                underlying_price
            )
            
            # Calculate moneyness for hover data
            moneyness_grid = strikes_grid / underlying_price
            
            # Add surface trace
            fig.add_trace(go.Surface(
                x=strikes_grid,
                y=expiries_grid * 365,  # Convert to days for better readability
                z=greeks_surfaces[greek_name],
                customdata=moneyness_grid,
                colorscale=config['color'],
                name=f"{config['name']} ({config['description']})",
                hovertemplate=hover_text,
                visible=config['visible'],
                showscale=True,
                colorbar=dict(
                    title=f"{config['name']} Value",
                    x=1.02,
                    len=0.8
                )
            ))
    
    # Add buttons for toggling between Greeks
    buttons = _create_toggle_buttons(greeks_config, greeks_view)
    
    # Update layout with proper styling and controls
    fig.update_layout(
        title=dict(
            text=f"Options Greeks Landscape - {ticker}<br><sub>Underlying Price: ${underlying_price:.2f}</sub>",
            x=0.5,
            font=dict(size=16)
        ),
        scene=dict(
            xaxis=dict(
                title=dict(text="Strike Price ($)", font=dict(size=12)),
                tickfont=dict(size=10)
            ),
            yaxis=dict(
                title=dict(text="Days to Expiry", font=dict(size=12)),
                tickfont=dict(size=10)
            ),
            zaxis=dict(
                title=dict(text="Greeks Value", font=dict(size=12)),
                tickfont=dict(size=10)
            ),
            camera=dict(
                eye=dict(x=1.5, y=1.5, z=1.2)
            ),
            aspectmode='cube'
        ),
        updatemenus=[
            dict(
                type="buttons",
                direction="left",
                buttons=buttons,
                pad={"r": 10, "t": 10},
                showactive=True,
                x=0.01,
                xanchor="left",
                y=1.02,
                yanchor="top"
            ),
        ],
        annotations=[
            dict(
                text="Select Greeks View:",
                showarrow=False,
                x=0.01,
                y=1.08,
                xref="paper",
                yref="paper",
                align="left",
                font=dict(size=12)
            )
        ],
        width=900,
        height=700,
        margin=dict(l=0, r=0, t=80, b=0)
    )
    
    return fig


def _create_hover_text(
    strikes_grid: Any,
    expiries_grid: Any, 
    greeks_values: Any,
    greek_name: str,
    underlying_price: float
) -> str:
    """
    Create detailed hover text for Greeks surface plots.
    
    Args:
        strikes_grid: Meshgrid of strike prices
        expiries_grid: Meshgrid of time to expiry values
        greeks_values: Greeks values for the surface
        greek_name: Name of the Greek being displayed
        underlying_price: Current underlying price
        
    Returns:
        HTML formatted hover template string
    """
    # Calculate moneyness for additional context
    moneyness_grid = strikes_grid / underlying_price
    
    hover_template = (
        f"<b>{greek_name.title()} Surface</b><br>"
        "Strike: $%{x:.2f}<br>"
        "Days to Expiry: %{y:.0f}<br>"
        f"{greek_name.title()}: %{{z:.4f}}<br>"
        "Moneyness: %{customdata:.3f}<br>"
        "<extra></extra>"
    )
    
    return hover_template


def _create_toggle_buttons(greeks_config: Dict[str, Dict], current_view: str) -> list:
    """
    Create toggle buttons for switching between different Greeks views.
    
    Args:
        greeks_config: Configuration dictionary for Greeks
        current_view: Currently selected view
        
    Returns:
        List of button configurations for Plotly updatemenus
    """
    buttons = []
    
    # Add "All" button to show all Greeks
    all_visible = [True] * len(greeks_config)
    buttons.append(dict(
        label="All Greeks",
        method="update",
        args=[
            {"visible": all_visible},
            {"title": "Options Greeks Landscape - All Greeks"}
        ]
    ))
    
    # Add individual Greek buttons
    for i, (greek_name, config) in enumerate(greeks_config.items()):
        visible = [False] * len(greeks_config)
        visible[i] = True
        
        buttons.append(dict(
            label=f"{config['name']} Only",
            method="update", 
            args=[
                {"visible": visible},
                {"title": f"Options Greeks Landscape - {config['name']} ({config['description']})"}
            ]
        ))
    
    return buttons