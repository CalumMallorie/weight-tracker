from flask import Blueprint, request, render_template, redirect, url_for, jsonify, current_app
import logging
from . import services
from typing import Dict, Any, List, Optional

# Set up logger
logger = logging.getLogger(__name__)

# Create blueprint for view routes
main = Blueprint('main', __name__)

# Create blueprint for API routes
api = Blueprint('api', __name__, url_prefix='/api')

@main.route('/', methods=['GET', 'POST'])
def index():
    """Main page for entering weight and viewing charts"""
    logger.info(f"Access to index page with method: {request.method}")
    
    # Get all categories
    categories = services.get_all_categories()
    
    # Default to first category (Body Mass) if available
    selected_category_id = int(request.args.get('category', '0')) if request.args.get('category') else None
    if not selected_category_id and categories:
        selected_category_id = categories[0].id
        
    # Get the category object
    selected_category = next((c for c in categories if c.id == selected_category_id), None)
    
    # Get processing type from request or default to 'none'
    processing_type = request.args.get('processing', 'none')
    
    # List of available processing types
    processing_types = services.get_available_processing_types()
    
    if request.method == 'POST':
        try:
            # Parse form data
            weight = float(request.form.get('weight', 0))
            unit = request.form.get('unit', 'kg')
            category_id = int(request.form.get('category', 0))
            reps = request.form.get('reps')
            
            # Validate weight
            if weight <= 0:
                raise ValueError("Weight must be greater than zero")
            
            # Convert reps to integer if provided
            if reps:
                reps = int(reps)
                if reps <= 0:
                    raise ValueError("Reps must be greater than zero")
            
            # Save the entry
            services.save_weight_entry(weight, unit, category_id, reps)
            logger.info("Weight entry saved successfully")
            
            # Redirect to maintain selected category and processing type
            return redirect(url_for(
                'main.index', 
                window=request.args.get('window', 'month'),
                category=category_id,
                processing=processing_type
            ))
            
        except (ValueError, TypeError) as e:
            # Handle input errors
            error_message = f"Invalid input: {str(e)}"
            logger.warning(f"Invalid form data: {str(e)}")
            
            # Re-render with error
            time_window = request.args.get('window', 'month')
            entries = services.get_entries_by_time_window(time_window, selected_category_id)
            plot_json = services.create_weight_plot(entries, time_window, processing_type)
            
            return render_template(
                'index.html', 
                entries=entries, 
                plot_json=plot_json, 
                time_window=time_window, 
                error=error_message,
                categories=categories,
                selected_category=selected_category,
                processing_types=processing_types,
                selected_processing=processing_type
            )
    
    # Handle GET request
    time_window = request.args.get('window', 'month')
    logger.info(f"Getting data for time window: {time_window}, category: {selected_category_id}")
    entries = services.get_entries_by_time_window(time_window, selected_category_id)
    plot_json = services.create_weight_plot(entries, time_window, processing_type)
    
    return render_template(
        'index.html', 
        entries=entries, 
        plot_json=plot_json, 
        time_window=time_window,
        categories=categories,
        selected_category=selected_category,
        processing_types=processing_types,
        selected_processing=processing_type
    )

@main.route('/entries', methods=['GET'])
def get_entries():
    """Page for viewing and managing entries"""
    logger.info("Access to entries management page")
    
    # Get category filter if provided
    category_id = request.args.get('category')
    if category_id:
        category_id = int(category_id)
    
    # Get all categories
    categories = services.get_all_categories()
    
    # Get entries, possibly filtered by category
    entries = services.get_all_entries(category_id)
    
    return render_template(
        'entries.html', 
        entries=entries, 
        categories=categories,
        selected_category_id=category_id
    )

@main.route('/categories', methods=['GET', 'POST'])
def manage_categories():
    """Page for managing weight categories"""
    logger.info(f"Access to categories management page with method: {request.method}")
    
    if request.method == 'POST':
        # Handle category creation
        name = request.form.get('name', '').strip()
        
        if name:
            try:
                services.get_or_create_category(name)
                logger.info(f"Category '{name}' created/updated successfully")
            except Exception as e:
                logger.error(f"Failed to create category: {str(e)}")
                return render_template(
                    'categories.html', 
                    categories=services.get_all_categories(),
                    error=f"Failed to create category: {str(e)}"
                )
                
        return redirect(url_for('main.manage_categories'))
    
    # GET request - show categories
    categories = services.get_all_categories()
    return render_template('categories.html', categories=categories)

@api.route('/entries', methods=['GET'])
def api_entries():
    """API endpoint to get all entries as JSON"""
    logger.info("API request for all entries")
    
    # Get category filter if provided
    category_id = request.args.get('category')
    if category_id:
        category_id = int(category_id)
    
    entries = services.get_all_entries(category_id)
    return jsonify([entry.to_dict() for entry in entries])

@api.route('/entries/<int:entry_id>', methods=['DELETE'])
def api_delete_entry(entry_id):
    """API endpoint to delete an entry"""
    logger.info(f"API request to delete entry {entry_id}")
    success = services.delete_entry(entry_id)
    logger.info(f"Delete entry {entry_id} result: {success}")
    return jsonify({'success': success})

@api.route('/categories', methods=['GET'])
def api_categories():
    """API endpoint to get all categories as JSON"""
    logger.info("API request for all categories")
    categories = services.get_all_categories()
    return jsonify([category.to_dict() for category in categories])

@api.route('/categories', methods=['POST'])
def api_create_category():
    """API endpoint to create a new category"""
    data = request.json
    
    if not data or 'name' not in data:
        return jsonify({'error': 'Name is required'}), 400
    
    name = data['name'].strip()
    if not name:
        return jsonify({'error': 'Name cannot be empty'}), 400
    
    try:
        category = services.get_or_create_category(name)
        return jsonify(category.to_dict()), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api.route('/categories/<int:category_id>', methods=['DELETE'])
def api_delete_category(category_id):
    """API endpoint to delete a category"""
    logger.info(f"API request to delete category {category_id}")
    success = services.delete_category(category_id)
    logger.info(f"Delete category {category_id} result: {success}")
    return jsonify({'success': success})

@api.route('/processing-types', methods=['GET'])
def api_processing_types():
    """API endpoint to get available processing types"""
    logger.info("API request for processing types")
    return jsonify(services.get_available_processing_types()) 