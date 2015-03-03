package gov.nist.spectrumbrowser.client;

import gov.nist.spectrumbrowser.common.AbstractSpectrumBrowser;
import gov.nist.spectrumbrowser.common.AbstractSpectrumBrowserService;
import gov.nist.spectrumbrowser.common.SpectrumBrowserCallback;

import java.util.HashMap;
import java.util.HashSet;
import java.util.Map;
import java.util.logging.Level;
import java.util.logging.Logger;

import com.google.gwt.core.client.EntryPoint;
import com.google.gwt.core.client.GWT;
import com.google.gwt.dom.client.HeadingElement;
import com.google.gwt.event.logical.shared.CloseEvent;
import com.google.gwt.event.logical.shared.CloseHandler;
import com.google.gwt.json.client.JSONParser;
import com.google.gwt.json.client.JSONValue;
import com.google.gwt.user.client.Window;
import com.google.gwt.user.client.Window.ClosingEvent;
import com.google.gwt.user.client.Window.ClosingHandler;
import com.google.gwt.user.client.ui.HTML;
import com.google.gwt.user.client.ui.HasHorizontalAlignment;
import com.google.gwt.user.client.ui.HorizontalPanel;
import com.google.gwt.user.client.ui.Image;
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

	
	
	private static HashMap<String,SensorInformation> sensorInformationTable = new HashMap<String,SensorInformation>();
	

	static {
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
								SpectrumBrowser.setSessionToken(jsonValue
										.isObject().get("SessionToken")
										.isString().stringValue());
								RootPanel rootPanel = RootPanel.get();

								rootPanel.clear();
								
								VerticalPanel rootVerticalPanel = new VerticalPanel();
								rootVerticalPanel.setHorizontalAlignment(HasHorizontalAlignment.ALIGN_CENTER);
								rootVerticalPanel.setWidth(Window.getClientWidth() + "px");
								
								
								
								HorizontalPanel hpanel = new HorizontalPanel();
								hpanel.setWidth(MAP_WIDTH  + "px");
								int height = 50;
								Image nistLogo = new Image( SpectrumBrowser.getIconsPath() + "nist-logo.png");
								nistLogo.setPixelSize((int)(215.0/95.0)*height, height);
								Image ntiaLogo = new Image(SpectrumBrowser.getIconsPath() +  "ntia-logo.png");
								ntiaLogo.setPixelSize(height, height);
								hpanel.setHorizontalAlignment(HasHorizontalAlignment.ALIGN_LEFT);
								hpanel.add(nistLogo);
								HTML html = new HTML("<h2>CAC Measured Spectrum Occupancy Database </h2>");
								hpanel.setHorizontalAlignment(HasHorizontalAlignment.ALIGN_CENTER);
								hpanel.add(html);
								hpanel.setHorizontalAlignment(HasHorizontalAlignment.ALIGN_RIGHT);
								hpanel.add(ntiaLogo);
							
								rootVerticalPanel.add(hpanel);
								VerticalPanel verticalPanel = new VerticalPanel();
								verticalPanel
										.setHorizontalAlignment(HasHorizontalAlignment.ALIGN_CENTER);
								verticalPanel.setStyleName("loginPanel");
								verticalPanel.setSpacing(20);
								rootVerticalPanel.add(verticalPanel);
								rootPanel.add(rootVerticalPanel);

								new SpectrumBrowserShowDatasets(
										SpectrumBrowser.this, verticalPanel);
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
		spectrumBrowserService.logOff(
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

	public static String getGeneratedDataPath(String sensorId) {
		SensorInformation si = sensorInformationTable.get(sensorId);
		if ( si == null) {
			logger.severe("getGeneratedDataPath: Null returned from sensorInformationTable for " + sensorId);
			return null;
		} else {
			return si.getBaseUrl() + "/generated/";
		}
	}

	@Override
	public boolean isUserLoggedIn() {
		return userLoggedIn;
	}

	public void setUserLoggedIn(boolean flag) {
		this.userLoggedIn = flag;
	}
	
	public static void addSensor(SensorInformation sensorInformation) {
		sensorInformationTable.put(sensorInformation.getId(),sensorInformation);
	}
	
	public static String getBaseUrl(String sensorId) {
		SensorInformation si = sensorInformationTable.get(sensorId);
		if ( si == null) {
			return null;
		} else {
			return si.getBaseUrl() + "/spectrumbrowser/";
		}
	}

	public static void clearSensorInformation() {
		logger.finer("clearSensorInformation");
		String sessionToken = getSessionToken();
		sensorInformationTable.clear();
		clearSessionTokens();
		// Restore the saved token to our web service.
		setSessionToken(sessionToken);
	}

	public static String getSessionTokenForSensor(String sensorId) {
		String url = sensorInformationTable.get(sensorId).getBaseUrl();
		logger.finer("getSessionTokenForSensor: " + sensorId + " / " + url);
		return getSessionToken(url);
	}
	
	public static String getBaseUrlAuthority(String sensorId) {
		SensorInformation si = sensorInformationTable.get(sensorId);
		if ( si == null) {
			return null;
		} else {
			return si.getBaseUrl();
		}
	}

	public static void logoffAllSensors() {
		spectrumBrowserService.logOff(new SpectrumBrowserCallback<String> () {

			@Override
			public void onSuccess(String result) {
				// TODO Auto-generated method stub
				
			}

			@Override
			public void onFailure(Throwable throwable) {
				logger.log(Level.SEVERE,"Problem logging off",throwable);
			}});
		for (String sensorId : SpectrumBrowser.sensorInformationTable.keySet())
			spectrumBrowserService.logOff(sensorId,new SpectrumBrowserCallback<String> () {

			@Override
			public void onSuccess(String result) {
			}

			@Override
			public void onFailure(Throwable throwable) {
				logger.log(Level.SEVERE,"Problem logging off",throwable);
				
			}});
	}

}
