package gov.nist.spectrumbrowser.client;

import java.util.logging.Logger;

import com.google.gwt.core.client.EntryPoint;
import com.google.gwt.core.client.GWT;
import com.google.gwt.dom.client.HeadingElement;
import com.google.gwt.user.client.Window;
import com.google.gwt.user.client.ui.PasswordTextBox;
import com.google.gwt.user.client.ui.PopupPanel;
import com.google.gwt.user.client.ui.RootPanel;
import com.google.gwt.user.client.ui.TextBox;
import com.google.gwt.user.client.ui.VerticalPanel;

/**
 * Entry point classes define <code>onModuleLoad()</code>.
 */
public class SpectrumBrowser implements EntryPoint {

	VerticalPanel verticalPanel;
	static Logger logger = Logger.getLogger("SpectrumBrowser");
	PasswordTextBox passwordEntry;
	TextBox nameEntry;
	String locationName;
	PopupPanel popupPanel = new PopupPanel();
	String sessionToken;
	HeadingElement helement;
	HeadingElement welcomeElement;
	static final String API_KEY = "AIzaSyDgnBNVM2l0MS0fWMXh3SCzBz6FJyiSodU";
	public static final int MAP_WIDTH = 800;
	public static final int MAP_HEIGHT = 800;
	
	
	

	/**
	 * Create a remote service proxy to talk to the server-side Greeting
	 * service.
	 */
	private static final String baseUrl = GWT.getModuleBaseURL();
	private static final SpectrumBrowserServiceAsync spectrumBrowserService = new SpectrumBrowserServiceAsyncImpl(
			baseUrl);
	public static final String LOGOFF_LABEL = "Log Off";
	public static final String ABOUT_LABEL = "About";
	public static final String HELP_LABEL = "Help";
	
	private static  String baseUrlAuthority ;
	
	private static String iconsPath;
	
	private static String generatedDataPath;
	
	private static String apiPath;
	
	static {
		logger.addHandler(new SpectrumBrowserLoggingHandler(spectrumBrowserService));
		String moduleName  = GWT.getModuleName();
		int index = baseUrl.indexOf("/" + moduleName);
		baseUrlAuthority = baseUrl.substring(0,index);
		logger.finest("baseUrlAuthority " + baseUrlAuthority);
		iconsPath = baseUrlAuthority + "/myicons/";
		generatedDataPath = baseUrlAuthority + "/generated/";
		apiPath = baseUrlAuthority + "/api/html/";
		
		logger.fine("iconsPath = " + iconsPath);
	}

	/**
	 * Display the error message and put up the login screen again.
	 * 
	 * @param errorMessage
	 */
	public void displayError(String errorMessage) {
		Window.alert(errorMessage);
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
		
		new LoginScreen(this).draw();
	}

	public String getSessionId() {
		return this.sessionToken;
	}
	
	public static String getBaseUrl() {
		return baseUrl;
	}
	
	public static String getBaseUrlAuthority() {
		return baseUrlAuthority;
	}

	public void logoff() {

		spectrumBrowserService.logOut(sessionToken,
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

	public void setSessionToken(String sessionToken) {
		this.sessionToken = sessionToken;
	}

	public static String getIconsPath() {
		return iconsPath;
	}
	
	public static String getGeneratedDataPath() {
		return generatedDataPath;
	}
	
	public static String getApiPath() {
		return apiPath;
	}

}
