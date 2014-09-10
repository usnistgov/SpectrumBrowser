package gov.nist.spectrumbrowser.client;

import java.util.logging.Logger;

import com.google.gwt.core.client.Scheduler;
import com.google.gwt.event.dom.client.ClickHandler;
import com.google.gwt.safehtml.shared.SafeHtmlBuilder;
import com.google.gwt.user.client.ui.MenuBar;
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
class AdminScreen implements SpectrumBrowserCallback {
	
	private VerticalPanel verticalPanel;
	private SpectrumBrowser spectrumBrowser;
	private static Logger logger = Logger.getLogger("SpectrumBrowser");
	
	public AdminScreen(VerticalPanel verticalPanel, SpectrumBrowser spectrumBrowser) {
		logger.finer("AdminScreen");
		this.verticalPanel = verticalPanel;
		this.spectrumBrowser = spectrumBrowser;
	}

	public void draw() {
		
		verticalPanel.clear();
		MenuBar menuBar = new MenuBar();
		SafeHtmlBuilder safeHtml = new SafeHtmlBuilder();
		menuBar.addItem(
				safeHtml.appendEscaped(SpectrumBrowser.LOGOFF_LABEL)
						.toSafeHtml(),
				new Scheduler.ScheduledCommand() {

					@Override
					public void execute() {
						spectrumBrowser.logoff();

					}
				});
		verticalPanel.add(menuBar);
		TextBox textBox = new TextBox();
		textBox.setText("Hello Julie. Happy Hacking.");
		verticalPanel.add(textBox);
		
	}

	@Override
	public void onSuccess(Object result) {
		// TODO Auto-generated method stub
		
	}

	@Override
	public void onFailure(Throwable throwable) {
		// TODO Auto-generated method stub
		
	}

}
