package gov.nist.spectrumbrowser.admin;

import gov.nist.spectrumbrowser.common.SpectrumBrowserCallback;
import gov.nist.spectrumbrowser.common.SpectrumBrowserScreen;

import java.util.logging.Level;
import java.util.logging.Logger;

import com.google.gwt.event.logical.shared.SelectionEvent;
import com.google.gwt.event.logical.shared.SelectionHandler;
import com.google.gwt.user.client.Timer;
import com.google.gwt.user.client.ui.Button;
import com.google.gwt.user.client.ui.HTML;
import com.google.gwt.user.client.ui.TabPanel;
import com.google.gwt.user.client.ui.VerticalPanel;

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
	private SpectrumBrowserScreen[] screens = new SpectrumBrowserScreen[3];

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
			OutboundPeers peers = new OutboundPeers(adminEntryPoint);
			screens[counter++] = peers;
			tabPanel.add(peers,peers.getEndLabel());
			InboundPeers inboundPeers = new InboundPeers(adminEntryPoint);
			screens[counter++] = inboundPeers;
			tabPanel.add(inboundPeers,inboundPeers.getEndLabel());
			
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
