from flask import Blueprint, request, render_template, redirect, url_for, jsonify, current_app
import logging
from . import services

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
    if request.method == 'POST':
        weight = request.form.get('weight')
        unit = request.form.get('unit', 'kg')
        notes = request.form.get('notes', '')
        
        logger.info(f"Form submission: weight={weight}, unit={unit}")
        
        try:
            weight = float(weight)
            if weight <= 0:
                raise ValueError("Weight must be greater than zero")
            
            services.save_weight_entry(weight, unit, notes)
            logger.info("Weight entry saved successfully")
        except (ValueError, TypeError) as e:
            # Handle input errors
            error_message = "Please enter a valid weight number"
            logger.warning(f"Invalid form data: {str(e)}")
            time_window = request.args.get('window', 'month')
            entries = services.get_entries_by_time_window(time_window)
            plot_json = services.create_weight_plot(entries, time_window)
            return render_template('index.html', entries=entries, plot_json=plot_json, 
                                  time_window=time_window, error=error_message)
            
        return redirect(url_for('main.index', window=request.args.get('window', 'month')))
    
    time_window = request.args.get('window', 'month')
    logger.info(f"Getting data for time window: {time_window}")
    entries = services.get_entries_by_time_window(time_window)
    plot_json = services.create_weight_plot(entries, time_window)
    
    return render_template('index.html', entries=entries, plot_json=plot_json, time_window=time_window)

@main.route('/entries', methods=['GET'])
def get_entries():
    """Page for viewing and managing entries"""
    logger.info("Access to entries management page")
    entries = services.get_all_entries()
    return render_template('entries.html', entries=entries)

@api.route('/entries', methods=['GET'])
def api_entries():
    """API endpoint to get all entries as JSON"""
    logger.info("API request for all entries")
    entries = services.get_all_entries()
    return jsonify([entry.to_dict() for entry in entries])

@api.route('/entries/<int:entry_id>', methods=['DELETE'])
def api_delete_entry(entry_id):
    """API endpoint to delete an entry"""
    logger.info(f"API request to delete entry {entry_id}")
    success = services.delete_entry(entry_id)
    logger.info(f"Delete entry {entry_id} result: {success}")
    return jsonify({'success': success}) 