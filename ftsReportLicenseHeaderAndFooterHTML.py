def ftsReportLicenseHeaderAndFooterHTML(oProductDetails):
  bLicensedForCommercialUse = oProductDetails.oLicense \
      and oProductDetails.oLicense.sUsageTypeDescription == "commercial use";
  sLicenseHeaderHTML = " ".join([
    oProductDetails.oLicense and (
      "Licensed to %s for %s." % (
        oProductDetails.oLicense.sLicenseeName,
        oProductDetails.oLicense.sUsageTypeDescription
      )
    ) or "",
    not bLicensedForCommercialUse and (
      "You may not use this version of BugId for commercial purposes. Please contact the author if you wish to "
      "use BugId commercially. Contact and licensing information can be found at the bottom of this report."
    ) or "",
  ]);
  sNonCommercialLicenseHTML = """
    <a rel="license" href="http://creativecommons.org/licenses/by-nc/4.0/">
      <img alt="Creative Commons License" style="vertical-align: middle; float: left;"
          original-src="https://i.creativecommons.org/l/by-nc/4.0/88x31.png"
          src="data:image/png;base64,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"/>
    </a>
    This copy of BugId is licensed under a <a rel="license" href="http://creativecommons.org/licenses/by-nc/4.0/">
    Creative Commons Attribution-NonCommercial 4.0 International License</a> %s.<br/>
    Please contact the author if you wish to %s.
""";
  sLicenseFooterHTML = (
    bLicensedForCommercialUse and (
      "This copy of BugId is licensed for commercial use by %s." % oProductDetails.oLicense.sLicenseeName
    ) or oProductDetails.oLicense and (
      sNonCommercialLicenseHTML % (
        # This copy is licensed under by-nc 4.0 ...
        "to %s" % oProductDetails.oLicense.sLicenseeName,
        # Please contact if you wish to ...
        "use BugId commercially",
      )
    ) or (
      sNonCommercialLicenseHTML % (
        # This copy is licensed under by-nc 4.0 ...
        "during a trial period",
        # Please contact if you wish to ...
        "continue to use BugId after the trial period",
      )
    )
  );
  return (sLicenseHeaderHTML, sLicenseFooterHTML);
