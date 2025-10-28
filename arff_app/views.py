import os
import tempfile
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.contrib import messages

def parse_arff_file(file_path):
    """
    Parse ARFF file and return data as list of lists
    """
    data = []
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
            lines = file.readlines()
        
        # Find data section
        in_data_section = False
        for line in lines:
            line = line.strip()
            
            # Skip empty lines and comments
            if not line or line.startswith('%'):
                continue
            
            # Start of data section
            if line.lower().startswith('@data'):
                in_data_section = True
                continue
                
            # Process data lines
            if in_data_section:
                if line and not line.startswith('@'):
                    # Split by comma and clean values
                    row = [val.strip().strip('"').strip("'") for val in line.split(',')]
                    data.append(row)
        
        return data
    
    except Exception as e:
        print(f"Error parsing ARFF file: {e}")
        return []

def home(request):
    """
    Home page - display upload form
    """
    return render(request, 'arff_app/upload.html')

def upload_arff(request):
    """
    Handle ARFF file upload and processing
    """
    if request.method == 'POST' and request.FILES.get('arff_file'):
        uploaded_file = request.FILES['arff_file']
        
        # Validate file extension
        if not uploaded_file.name.lower().endswith('.arff'):
            messages.error(request, 'Por favor, sube un archivo con extensión .arff')
            return redirect('home')
        
        try:
            # Save uploaded file temporarily
            with tempfile.NamedTemporaryFile(delete=False, suffix='.arff') as tmp_file:
                for chunk in uploaded_file.chunks():
                    tmp_file.write(chunk)
                tmp_path = tmp_file.name
            
            # Parse ARFF file
            data = parse_arff_file(tmp_path)
            
            if not data:
                messages.error(request, 'No se pudieron extraer datos del archivo ARFF o el archivo está vacío')
                # Clean up temporary file
                os.unlink(tmp_path)
                return redirect('home')
            
            # Get first 20 columns of each row
            first_20_columns = []
            for row in data:
                # Ensure we have at least 20 columns, pad with empty strings if needed
                padded_row = row + [''] * (20 - len(row)) if len(row) < 20 else row[:20]
                first_20_columns.append(padded_row)
            
            # Create column names
            column_names = [f'Columna {i+1}' for i in range(20)]
            
            # Clean up temporary file
            os.unlink(tmp_path)
            
            # Prepare context for template
            context = {
                'filename': uploaded_file.name,
                'data': first_20_columns[:100],  # Limit to first 100 rows for display
                'column_names': column_names,
                'total_rows': len(data),
                'total_columns': len(data[0]) if data else 0,
                'displayed_rows': min(100, len(data)),
            }
            
            return render(request, 'arff_app/results.html', context)
            
        except Exception as e:
            # Clean up temporary file in case of error
            try:
                os.unlink(tmp_path)
            except:
                pass
                
            messages.error(request, f'Error procesando el archivo: {str(e)}')
            return redirect('home')
    
    # If not POST or no file, redirect to home
    return redirect('home')

def api_upload_arff(request):
    """
    API endpoint for file upload (JSON response)
    """
    if request.method == 'POST' and request.FILES.get('arff_file'):
        uploaded_file = request.FILES['arff_file']
        
        if not uploaded_file.name.lower().endswith('.arff'):
            return JsonResponse({
                'error': 'Solo se permiten archivos .arff',
                'success': False
            }, status=400)
        
        try:
            # Save uploaded file temporarily
            with tempfile.NamedTemporaryFile(delete=False, suffix='.arff') as tmp_file:
                for chunk in uploaded_file.chunks():
                    tmp_file.write(chunk)
                tmp_path = tmp_file.name
            
            # Parse ARFF file
            data = parse_arff_file(tmp_path)
            
            if not data:
                os.unlink(tmp_path)
                return JsonResponse({
                    'error': 'No se pudieron extraer datos del archivo',
                    'success': False
                }, status=400)
            
            # Get first 20 columns of first 50 rows
            first_20_columns = []
            for row in data[:50]:  # Limit to first 50 rows for API response
                padded_row = row + [''] * (20 - len(row)) if len(row) < 20 else row[:20]
                first_20_columns.append(padded_row)
            
            # Clean up temporary file
            os.unlink(tmp_path)
            
            return JsonResponse({
                'filename': uploaded_file.name,
                'data': first_20_columns,
                'total_rows': len(data),
                'total_columns': len(data[0]) if data else 0,
                'displayed_rows': len(first_20_columns),
                'success': True
            })
            
        except Exception as e:
            # Clean up temporary file in case of error
            try:
                os.unlink(tmp_path)
            except:
                pass
                
            return JsonResponse({
                'error': f'Error procesando el archivo: {str(e)}',
                'success': False
            }, status=500)
    
    return JsonResponse({
        'error': 'No se proporcionó archivo',
        'success': False
    }, status=400)

# View para manejar errores 404
def handler404(request, exception):
    return render(request, 'arff_app/404.html', status=404)

# View para manejar errores 500  
def handler500(request):
    return render(request, 'arff_app/500.html', status=500)





