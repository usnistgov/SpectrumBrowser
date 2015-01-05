package gov.nist.spectrumbrowser.admin;

import gov.nist.spectrumbrowser.common.SpectrumBrowserCallback;
import gov.nist.spectrumbrowser.common.SpectrumBrowserScreen;

import java.util.logging.Level;
import java.util.logging.Logger;

import com.google.gwt.core.client.GWT;
import com.google.gwt.core.client.Scheduler;
import com.google.gwt.event.dom.client.ClickEvent;
import com.google.gwt.event.dom.client.ClickHandler;
import com.google.gwt.event.logical.shared.SelectionEvent;
import com.google.gwt.event.logical.shared.SelectionHandler;
import com.google.gwt.safehtml.shared.SafeHtmlBuilder;
import com.google.gwt.user.client.Command;
import com.google.gwt.user.client.Timer;
import com.google.gwt.user.client.ui.Grid;
import com.google.gwt.user.client.ui.HTML;
import com.google.gwt.user.client.ui.MenuBar;
import com.google.gwt.user.client.ui.TabPanel;
import com.google.gwt.user.client.ui.TextBox;
import com.google.gwt.user.client.ui.VerticalPanel;
import com.google.gwt.user.client.ui.Button;

/**
 * Sample admin screen.
 * 
 * @author local
 *
 *         Note: this is a sample admin screen class. It is structured in the
 *         same way as the other screens (i.e. it implements
 *         SpectrumBrowserCallback). Right now it does nothing useful.
 */
class AdminScreen implements SpectrumBrowserCallback<String> {

	private VerticalPanel verticalPanel;
	private Admin adminEntryPoint;
	private static Logger logger = Logger.getLogger("SpectrumBrowser");
	private Button logOutButton;
	private TabPanel tabPanel;
	private SpectrumBrowserScreen[] screens = new SpectrumBrowserScreen[1];

	public AdminScreen(VerticalPanel verticalPanel, Admin adminEntryPoint) {
		logger.finer("AdminScreen");
		this.verticalPanel = verticalPanel;
		this.adminEntryPoint = adminEntryPoint;
	}

	public void draw() {
		try {

			verticalPanel.clear();
			HTML html = new HTML(
					"<h1>Hello administrator. Please select action to proceed</h1> ",
					true);
			verticalPanel.add(html);

			tabPanel = new TabPanel();

			int counter = 0;
			SystemConfig systemConfig = new SystemConfig(adminEntryPoint);
			screens[counter++] = systemConfig;

			tabPanel.add(systemConfig, systemConfig.getEndLabel());
			tabPanel.addSelectionHandler(new SelectionHandler<Integer>() {

				@Override
				public void onSelection(SelectionEvent<Integer> event) {
					int selection = event.getSelectedItem();
					
					screens[selection].draw();
				}
			});
			
			verticalPanel.add(tabPanel);
			
			Timer timer = new Timer() {

				@Override
				public void run() {
					tabPanel.selectTab(0);
				}  };

			timer.schedule(500);
		} catch (Throwable th) {
			logger.log(Level.SEVERE, "Problem drawing Admin Screen", th);
			adminEntryPoint.logoff();
		}

	}

	@Override
	public void onSuccess(String result) {
		// TODO Auto-generated method stub

	}

	@Override
	public void onFailure(Throwable throwable) {
		// TODO Auto-generated method stub

	}

}
