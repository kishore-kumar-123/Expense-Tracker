import os
import datetime
import urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler
import db

class ExpenseTrackerServer(BaseHTTPRequestHandler):

    def do_GET(self):
        """Handle HTTP GET Requests."""
        parsed_url = urllib.parse.urlparse(self.path)
        path = parsed_url.path
        query_params = urllib.parse.parse_qs(parsed_url.query)

        # 1. Serve CSS file
        if path == '/style.css':
            self.serve_file('style.css', 'text/css')
            return

        # 2. Serve Homepage
        if path == '/' or path == '/index.html':
            self.serve_homepage(query_params)
            return

        # 3. Handle 404 Not Found
        self.send_response(404)
        self.end_headers()
        self.wfile.write(b'Page Not Found')

    def do_POST(self):
        """Handle HTTP POST Requests (Form Submissions)."""
        parsed_url = urllib.parse.urlparse(self.path)
        path = parsed_url.path

        # Read form payload
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length).decode('utf-8')
        form_data = urllib.parse.parse_qs(body)

        # Handle Add Expense Form
        if path == '/add-expense':
            expense_date = form_data.get('date', [''])[0]
            category = form_data.get('category', [''])[0]
            amount = form_data.get('amount', ['0'])[0]
            description = form_data.get('description', [''])[0]

            if expense_date and category and amount:
                db.add_expense(expense_date, category, amount, description)

            self.redirect('/')
            return

        # Handle Delete Expense Button
        if path == '/delete-expense':
            expense_id = form_data.get('expense_id', [''])[0]
            if expense_id:
                db.delete_expense(expense_id)

            self.redirect('/')
            return

        self.send_response(404)
        self.end_headers()

    def serve_homepage(self, query_params):
        """Render index.html page with database contents."""
        current_month = datetime.date.today().month

        # Parse selected month parameter
        try:
            selected_month = int(query_params.get('month', [current_month])[0])
            if selected_month < 1 or selected_month > 12:
                selected_month = current_month
        except (ValueError, IndexError):
            selected_month = current_month

        # Fetch data from MySQL
        expenses = db.get_all_expenses()
        category_summary = db.get_category_summary()
        monthly_total = db.get_monthly_summary(selected_month)

        # Render All Expenses Rows
        all_expenses_html = ""
        if expenses:
            for item in expenses:
                date_formatted = str(item['expense_date'])
                amount_formatted = f"{item['amount']:.2f}"
                desc = item['description'] if item['description'] else ''
                all_expenses_html += f"""
                <tr>
                    <td>{item['expense_id']}</td>
                    <td>{date_formatted}</td>
                    <td>{html_escape(item['category'])}</td>
                    <td>₹{amount_formatted}</td>
                    <td>{html_escape(desc)}</td>
                    <td>
                        <form action="/delete-expense" method="POST" style="margin:0;">
                            <input type="hidden" name="expense_id" value="{item['expense_id']}">
                            <button type="submit" class="btn-delete">Delete</button>
                        </form>
                    </td>
                </tr>
                """
        else:
            all_expenses_html = "<tr><td colspan='6' style='text-align:center;'>No expenses found.</td></tr>"

        # Render Category Summary Rows
        category_summary_html = ""
        if category_summary:
            for cat in category_summary:
                cat_total = f"{cat['total']:.2f}"
                category_summary_html += f"""
                <tr>
                    <td>{html_escape(cat['category'])}</td>
                    <td>₹{cat_total}</td>
                </tr>
                """
        else:
            category_summary_html = "<tr><td colspan='2' style='text-align:center;'>No category data.</td></tr>"

        # Load HTML template
        with open('index.html', 'r', encoding='utf-8') as file:
            html = file.read()

        # Update Month Dropdown options
        for m in range(1, 13):
            placeholder = f"{{{{MONTH_{m}}}}}"
            selected_attr = "selected" if m == selected_month else ""
            html = html.replace(placeholder, selected_attr)

        # Replace dynamic data in HTML
        html = html.replace("{{SELECTED_MONTH_NUMBER}}", str(selected_month))
        html = html.replace("{{MONTHLY_TOTAL}}", f"{monthly_total:.2f}")
        html = html.replace("{{CATEGORY_SUMMARY_ROWS}}", category_summary_html)
        html = html.replace("{{ALL_EXPENSES_ROWS}}", all_expenses_html)

        # Return HTTP 200 OK Response
        content_bytes = html.encode('utf-8')
        self.send_response(200)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.send_header('Content-Length', str(len(content_bytes)))
        self.end_headers()
        self.wfile.write(content_bytes)

    def serve_file(self, filename, content_type):
        """Helper to serve static files like CSS."""
        if os.path.exists(filename):
            with open(filename, 'rb') as f:
                content = f.read()
            self.send_response(200)
            self.send_header('Content-Type', content_type)
            self.send_header('Content-Length', str(len(content)))
            self.end_headers()
            self.wfile.write(content)
        else:
            self.send_response(404)
            self.end_headers()

    def redirect(self, location):
        """Helper for HTTP 303 Redirect."""
        self.send_response(303)
        self.send_header('Location', location)
        self.end_headers()

def html_escape(text):
    """Sanitize strings for HTML rendering."""
    if not text:
        return ""
    return str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;").replace("'", "&#39;")

def main():
    print("Initializing Database...")
    db.init_db()
    print("Database ready!")

    port = 8000
    server_address = ('', port)
    httpd = HTTPServer(server_address, ExpenseTrackerServer)
    print(f"Expense Tracker running at: http://localhost:{port}")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping server...")
        httpd.server_close()

if __name__ == '__main__':
    main()
