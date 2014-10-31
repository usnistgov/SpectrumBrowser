package gov.nist.spectrumbrowser.admin;

import gov.nist.spectrumbrowser.common.AbstractSpectrumBrowserService;
import gov.nist.spectrumbrowser.common.SpectrumBrowserCallback;
import gov.nist.spectrumbrowser.common.SpectrumBrowserLoggingHandler;

import java.util.logging.Level;
import java.util.logging.Logger;

import com.google.gwt.core.client.EntryPoint;
import com.google.gwt.core.client.GWT;
import com.google.gwt.core.client.Scheduler;
import com.google.gwt.dom.client.Document;
import com.google.gwt.dom.client.HeadingElement;
import com.google.gwt.event.dom.client.ClickEvent;
import com.google.gwt.event.dom.client.ClickHandler;
import com.google.gwt.json.client.JSONObject;
import com.google.gwt.json.client.JSONParser;
import com.google.gwt.json.client.JSONValue;
import com.google.gwt.safehtml.shared.SafeHtmlBuilder;
import com.google.gwt.user.client.Window;
import com.google.gwt.user.client.ui.Button;
import com.google.gwt.user.client.ui.HasHorizontalAlignment;
import com.google.gwt.user.client.ui.HorizontalPanel;
import com.google.gwt.user.client.ui.Label;
import com.google.gwt.user.client.ui.MenuBar;
import com.google.gwt.user.client.ui.PasswordTextBox;
import com.google.gwt.user.client.ui.PopupPanel;
import com.google.gwt.user.client.ui.RootPanel;
import com.google.gwt.user.client.ui.TextBox;
import com.google.gwt.user.client.ui.VerticalPanel;

/**
 * Sample admin screen.
 * @author local
 *
 *Note: this is a sample admin screen class. It is structured in the same
 *way as the other screens (i.e. it implements SpectrumBrowserCallback). 
 *Right now it does nothing useful.
 */
class Admin implements  EntryPoint {
	
	private VerticalPanel verticalPanel;
	private static Logger logger;
	PasswordTextBox passwordEntry;
	TextBox nameEntry;
	String locationName;
	PopupPanel popupPanel = new PopupPanel();
	String sessionToken;
	HeadingElement helement;
	HeadingElement welcomeElement;
	private static String baseUrlAuthority;
	private static String iconsPath;
	
	String HEADING_TEXT = "DOC Measured Spectrum Occupancy Database Administrator Interface";
	String WELCOME_TEXT = "You are not very welcome here unless you are a database administrator";
	

	private static final String baseUrl = GWT.getModuleBaseURL();
	public static final String LOGOFF_LABEL = "Logoff";
	private static AdminService adminService = new AdminServiceImpl(baseUrl);
	static {
		String moduleName  = GWT.getModuleName();
		logger = Logger.getLogger("SpectrumBrowser");
		int index = baseUrl.indexOf("/" + moduleName);
		baseUrlAuthority = baseUrl.substring(0,index);
		logger.addHandler(new SpectrumBrowserLoggingHandler(baseUrlAuthority));

		logger.finest("baseUrlAuthority " + baseUrlAuthority);
		logger.finest("baseURL = " + baseUrl);
		iconsPath = baseUrlAuthority + "/myicons/";
		logger.fine("iconsPath = " + iconsPath);
	}

	public void draw() {
		RootPanel.get().clear(true);
		helement = Document.get().createHElement(1);
		helement.setInnerText(HEADING_TEXT);
	    RootPanel.get().getElement().appendChild(helement);
	    welcomeElement = Document.get().createHElement(2);
	    welcomeElement.setInnerText(WELCOME_TEXT);
	    RootPanel.get().getElement().appendChild(welcomeElement);
		verticalPanel = new VerticalPanel();
		verticalPanel.setHorizontalAlignment(HasHorizontalAlignment.ALIGN_CENTER);
		verticalPanel.setStyleName("loginPanel");
		verticalPanel.setSpacing(20);
	    RootPanel.get().add(verticalPanel);
		HorizontalPanel nameField = new HorizontalPanel();
		// Should use internationalization. for now just hard code it.
		Label nameLabel = new Label("User Name");
		nameLabel.setWidth("150px");
		nameField.add(nameLabel);
		nameEntry = new TextBox();
		nameEntry.setText("admin");
		nameEntry.setWidth("150px");
		nameField.add(nameEntry);
		verticalPanel.add(nameField);

		HorizontalPanel passwordField = new HorizontalPanel();
		Label passwordLabel = new Label("Password");
		passwordLabel.setWidth("150px");
		passwordField.add(passwordLabel);
		passwordEntry = new PasswordTextBox();
		passwordEntry.setWidth("150px");
		passwordField.add(passwordLabel);
		passwordField.add(passwordEntry);
		verticalPanel.add(passwordField);
		

		 Button sendButton = new Button("Log in");
		// We can add style names to widgets
		sendButton.addStyleName("sendButton");
		verticalPanel.add(sendButton);
			
		// Add the nameField and sendButton to the RootPanel
		// Use RootPanel.get() to get the entire body element

		// Focus the cursor on the name field when the app loads
		nameEntry.setFocus(true);
		nameEntry.selectAll();

		sendButton.addClickHandler(new SendNamePasswordToServer());
		
	}

	class SendNamePasswordToServer implements ClickHandler {

		@Override
		public void onClick(ClickEvent clickEvent) {
			String name = nameEntry.getValue();
			String password = passwordEntry.getValue();
			logger.finer("SendNamePasswordToServer: " + name);
			if (name == null || name.length() == 0) {
				Window.alert("Name is mandatory");
				return;
			}
			
			adminService.authenticate(
					name,password,  "admin",
					new SpectrumBrowserCallback<String>() {

						@Override
						public void onFailure(Throwable errorTrace) {
							logger.log(Level.SEVERE,
									"Error sending request to the server",errorTrace);
							Window.alert("Error communicating with the server.");
						
						
						}

						@Override
						public void onSuccess(String result) {
							try {
							JSONValue jsonValue = JSONParser.parseStrict(result);
							JSONObject jsonObject = jsonValue.isObject();
							String res = jsonObject.get("status").isString().stringValue();
							if (res.startsWith("OK")) {
								sessionToken = jsonObject.get("sessionId").isString().stringValue();
								verticalPanel.clear();
								helement.removeFromParent();
								welcomeElement.removeFromParent();
								new AdminScreen(verticalPanel, Admin.this).draw();
							} else {
								Window.alert("Username or Password is incorrect. Please try again");
							}
							} catch (Throwable ex) {
								Window.alert("Problem parsing json");
							}
						}
					});

		}

	}

	@Override
	public void onModuleLoad() {
		// TODO Auto-generated method stub
		draw();
		
	}

	public void logoff() {
		adminService.logOut(sessionToken, new SpectrumBrowserCallback<String> () {

			@Override
			public void onSuccess(String result) {
				RootPanel.get().clear();
				onModuleLoad();
			}

			@Override
			public void onFailure(Throwable throwable) {
				Window.alert("Error communicating with server");	
				onModuleLoad();
			}
			
		});
	}

}
