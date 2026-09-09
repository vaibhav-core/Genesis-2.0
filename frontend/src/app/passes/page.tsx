"use client";

import { GENESIS_START, PASS_UNLOCK_DATE } from "@/config/genesis";
import { Countdown, PageShell, PassCard, SectionHeading } from "@/components/genesis-ui";
import { useSyncExternalStore } from "react";

const subscribeToClock = (onChange: () => void) => { const timer = window.setInterval(onChange, 1000); return () => window.clearInterval(timer); };
export default function PassesPage() { const unlocked = useSyncExternalStore(subscribeToClock, () => Date.now() >= new Date(PASS_UNLOCK_DATE).getTime(), () => false); return <PageShell><main className="page-main"><section className="pass-heading"><span className="eyebrow">YOUR ENTRY</span><h1>Genesis<br /><em>Pass.</em></h1>{!unlocked ? <><p>Passes unlock when Genesis begins.</p><Countdown target={GENESIS_START} /></> : <p>Find your place in the beginning.</p>}</section><section className="section pass-section"><SectionHeading kicker={unlocked ? "ACCESS OPEN" : "ACCESS LOCKED"} title={unlocked ? "Get your Genesis pass." : "Genesis Pass — Locked"} />{unlocked ? <div className="pass-form"><label htmlFor="identifier">Enter roll number or name</label><input id="identifier" placeholder="e.g. 24ME001" /><button className="button" type="button">Generate pass <span>↗</span></button><PassCard /></div> : <p className="locked-note">The pass desk opens at the exact moment Genesis begins.</p>}</section></main></PageShell> }