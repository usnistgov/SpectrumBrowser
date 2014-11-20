package gov.nist.spectrumbrowser.client;

import gov.nist.spectrumbrowser.common.AbstractSpectrumBrowser;
import gov.nist.spectrumbrowser.common.AbstractSpectrumBrowserService;
import gov.nist.spectrumbrowser.common.SpectrumBrowserCallback;

import java.util.logging.Logger;

import com.google.gwt.core.client.EntryPoint;
import com.google.gwt.dom.client.HeadingElement;
import com.google.gwt.user.client.Window;
import com.google.gwt.user.client.ui.RootPanel;

/**
 * Entry point classes define <code>onModuleLoad()</code>.
 */
public class SpectrumBrowser extends AbstractSpectrumBrowser  implements EntryPoint {

	HeadingElement helement;
	HeadingElement welcomeElement;
	private boolean userLoggedIn;
	static final String API_KEY = "AIzaSyDgnBNVM2l0MS0fWMXh3SCzBz6FJyiSodU";
	public static final int MAP_WIDTH = 800;
	public static final int MAP_HEIGHT = 800;
	private static final String generatedDataPath = getBaseUrlAuthority() + "/generated/";
	private static final SpectrumBrowserServiceAsync spectrumBrowserService = new SpectrumBrowserServiceAsyncImpl(getBaseUrl());
	public static final String LOGOFF_LABEL = "Log Off";
	public static final String ABOUT_LABEL = "About";
	public static final String HELP_LABEL = "Help";
	private static final Logger logger = Logger.getLogger("SpectrumBrowser");


	

	/**
	 * Display the error message and put up the login screen again.
	 * 
	 * @param errorMessage
	 */
	public void displayError(String errorMessage) {
		Window.alert(errorMessage);
		if ( this.isUserLoggedIn()) logoff();

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
