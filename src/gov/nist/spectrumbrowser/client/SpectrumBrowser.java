package gov.nist.spectrumbrowser.client;

import gov.nist.spectrumbrowser.common.AbstractSpectrumBrowser;
import gov.nist.spectrumbrowser.common.AbstractSpectrumBrowserService;
import gov.nist.spectrumbrowser.common.SpectrumBrowserCallback;

import java.util.logging.Level;
import java.util.logging.Logger;

import com.google.gwt.core.client.EntryPoint;
import com.google.gwt.core.client.GWT;
import com.google.gwt.dom.client.HeadingElement;
import com.google.gwt.json.client.JSONParser;
import com.google.gwt.json.client.JSONValue;
import com.google.gwt.user.client.Window;
import com.google.gwt.user.client.ui.HasHorizontalAlignment;
import com.google.gwt.user.client.ui.RootPanel;
import com.google.gwt.user.client.ui.VerticalPanel;

/**
 * Entry point classes define <code>onModuleLoad()</code>.
 */
public class SpectrumBrowser extends AbstractSpectrumBrowser implements
		EntryPoint {

	HeadingElement helement;
	HeadingElement welcomeElement;
	private boolean userLoggedIn;
	public static final int MAP_WIDTH = 800;
	public static final int MAP_HEIGHT = 800;
	private static final Logger logger = Logger.getLogger("SpectrumBrowser");

	private static final SpectrumBrowserServiceAsync spectrumBrowserService = new SpectrumBrowserServiceAsyncImpl(
			getBaseUrl());

	/**
	 * Create a remote service proxy to talk to the server-side Greeting
	 * service.
	 */

	public static final String LOGOFF_LABEL = "Log Off";
	public static final String ABOUT_LABEL = "About";
	public static final String HELP_LABEL = "Help";

	private static String generatedDataPath;

	static {
		generatedDataPath = getBaseUrlAuthority() + "/generated/";
		GWT.setUncaughtExceptionHandler(new GWT.UncaughtExceptionHandler() {
			public void onUncaughtException(Throwable e) {
				logger.log(Level.SEVERE, "Uncaught Exception", e);
			}
		});
	}

	/**
	 * Display the error message and put up the login screen again.
	 * 
	 * @param errorMessage
	 */
	public void displayError(String errorMessage) {
		Window.alert(errorMessage);
		if (this.isUserLoggedIn())
			logoff();
	}

	SpectrumBrowserServiceAsync getSpectrumBrowserService() {
		return spectrumBrowserService;
	}

	/**
	 * This is the entry point method.
	 */
	@Override
	public void onModuleLoad() {
		logger.fine("onModuleLoad");
		spectrumBrowserService
				.isAuthenticationRequired(new SpectrumBrowserCallback<String>() {

					@Override
					public void onSuccess(String result) {
						try {
							logger.finer("Result: " + result);
							JSONValue jsonValue = JSONParser
									.parseLenient(result);
							boolean isAuthenticationRequired = jsonValue
									.isObject().get("AuthenticationRequired")
									.isBoolean().booleanValue();
							if (isAuthenticationRequired) {
								new LoginScreen(SpectrumBrowser.this).draw();
							} else {
								logger.fine("Authentication not required -- drawing maps");
								SpectrumBrowser.this.setSessionToken(jsonValue
										.isObject().get("SessionToken")
										.isString().stringValue());
								RootPanel rootPanel = RootPanel.get();

								rootPanel.clear();
								VerticalPanel verticalPanel = new VerticalPanel();
								verticalPanel
										.setHorizontalAlignment(HasHorizontalAlignment.ALIGN_CENTER);
								verticalPanel.setStyleName("loginPanel");
								verticalPanel.setSpacing(20);
								rootPanel.add(verticalPanel);
								new SpectrumBrowserShowDatasets(
										SpectrumBrowser.this, verticalPanel)
										.draw();
							}
						} catch (Throwable th) {
							logger.log(Level.SEVERE, "Error Parsing JSON", th);
						}
					}

					@Override
					public void onFailure(Throwable throwable) {
						Window.alert("Error contacting server. Please try later");

					}
				});

	}

	public void logoff() {
		spectrumBrowserService.logOut(getSessionId(),
				new SpectrumBrowserCallback<String>() {

					@Override
					public void onFailure(Throwable caught) {
						RootPanel.get().clear();
						onModuleLoad();
					}

					@Override
					public void onSuccess(String result) {
						// TODO Auto-generated method stub
						RootPanel.get().clear();
						onModuleLoad();
					}
				});
	}

	public static String getGeneratedDataPath() {
		return generatedDataPath;
	}

	@Override
	public boolean isUserLoggedIn() {
		return userLoggedIn;
	}

	public void setUserLoggedIn(boolean flag) {
		this.userLoggedIn = flag;
	}

}
